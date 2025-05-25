import os
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from pygit.utils import (
    get_head_commit, get_ref, read_index, write_index,
    read_tree, get_object, get_commit_info, hash_object,
    update_ref, get_branch_name, create_tree_from_index
)
from pygit.config import get_pygit_dir, get_repo_root

console = Console()

def merge(branch_name, no_ff=False):
    """Join two or more development histories together."""
    try:
        pygit_dir = get_pygit_dir()
        repo_root = get_repo_root()
        
        # Check if branch exists
        branch_path = pygit_dir / "refs" / "heads" / branch_name
        
        if not branch_path.exists():
            console.print(f"[yellow]Branch '{branch_name}' does not exist[/yellow]")
            return
        
        # Get the current branch
        current_branch = get_branch_name()
        
        if current_branch == "HEAD detached":
            console.print("[yellow]Cannot merge in detached HEAD state[/yellow]")
            return
        
        if current_branch == branch_name:
            console.print(f"[yellow]Cannot merge a branch into itself[/yellow]")
            return
        
        # Get the commit that the branch points to
        with open(branch_path, 'r') as f:
            branch_commit = f.read().strip()
        
        # Get the current HEAD commit
        head_commit = get_head_commit()
        
        if not head_commit:
            console.print("[yellow]Cannot merge: no commits on current branch[/yellow]")
            return
        
        # Check if this is a fast-forward merge
        is_ancestor = is_commit_ancestor(head_commit, branch_commit)
        
        if is_ancestor and not no_ff:
            # Fast-forward merge
            console.print("[green]Fast-forward merge[/green]")
            
            # Update the current branch to point to the target branch's commit
            update_ref(f"heads/{current_branch}", branch_commit)
            
            # Update working directory
            commit_info = get_commit_info(branch_commit)
            update_working_directory(commit_info["tree"])
            
            console.print(f"[green]Successfully merged branch '{branch_name}'[/green]")
            return
        
        # Find the merge base (common ancestor)
        merge_base = find_merge_base(head_commit, branch_commit)
        
        if not merge_base:
            console.print("[yellow]Cannot find common ancestor for merge[/yellow]")
            return
        
        # Perform a three-way merge
        console.print(f"[green]Merging branch '{branch_name}' into '{current_branch}'[/green]")
        
        # Get trees for all three commits
        base_tree = read_tree(get_commit_info(merge_base)["tree"])
        head_tree = read_tree(get_commit_info(head_commit)["tree"])
        branch_tree = read_tree(get_commit_info(branch_commit)["tree"])
        
        # Perform the merge
        conflicts = perform_merge(base_tree, head_tree, branch_tree)
        
        if conflicts:
            console.print("[yellow]Merge conflicts detected:[/yellow]")
            for path in conflicts:
                console.print(f"  {path}")
            console.print("\nFix conflicts and then commit the result.")
            return
        
        # Create a merge commit
        index = read_index()
        tree_hash = create_tree_from_index(index)
        
        # Get user information
        import os
        name = os.environ.get("GIT_AUTHOR_NAME", "Unknown")
        email = os.environ.get("GIT_AUTHOR_EMAIL", "unknown@example.com")
        author = f"{name} <{email}>"
        
        # Create the commit object
        import time
        timestamp = int(time.time())
        timezone = time.strftime("%z")
        
        commit_content = f"tree {tree_hash}\n"
        commit_content += f"parent {head_commit}\n"
        commit_content += f"parent {branch_commit}\n"
        commit_content += f"author {author} {timestamp} {timezone}\n"
        commit_content += f"committer {author} {timestamp} {timezone}\n\n"
        commit_content += f"Merge branch '{branch_name}' into {current_branch}\n"
        
        # Hash and store the commit
        commit_hash = hash_object(commit_content.encode(), "commit")
        
        # Update the current branch reference
        update_ref(f"heads/{current_branch}", commit_hash)
        
        console.print(f"[green]Successfully merged branch '{branch_name}'[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

def is_commit_ancestor(ancestor_hash, descendant_hash):
    """Check if one commit is an ancestor of another."""
    # Simple BFS to find if ancestor is reachable from descendant
    visited = set()
    queue = [descendant_hash]
    
    while queue:
        commit = queue.pop(0)
        
        if commit == ancestor_hash:
            return True
        
        if commit in visited:
            continue
        
        visited.add(commit)
        
        try:
            commit_info = get_commit_info(commit)
            queue.extend(commit_info.get("parents", []))
        except Exception:
            pass
    
    return False

def find_merge_base(commit1, commit2):
    """Find the common ancestor of two commits."""
    # Get all ancestors of commit1
    ancestors1 = set()
    queue = [commit1]
    
    while queue:
        commit = queue.pop(0)
        
        if commit in ancestors1:
            continue
        
        ancestors1.add(commit)
        
        try:
            commit_info = get_commit_info(commit)
            queue.extend(commit_info.get("parents", []))
        except Exception:
            pass
    
    # Check if commit2 or any of its ancestors are in ancestors1
    queue = [commit2]
    visited = set()
    
    while queue:
        commit = queue.pop(0)
        
        if commit in visited:
            continue
        
        if commit in ancestors1:
            return commit
        
        visited.add(commit)
        
        try:
            commit_info = get_commit_info(commit)
            queue.extend(commit_info.get("parents", []))
        except Exception:
            pass
    
    return None

def update_working_directory(tree_hash):
    """Update the working directory to match the given tree."""
    repo_root = get_repo_root()
    
    # Read the tree
    tree_files = read_tree(tree_hash)
    
    # Read current index
    index = read_index()
    
    # Track changes for the new index
    new_index = {}
    
    with Progress() as progress:
        task = progress.add_task("[green]Updating working directory...", total=len(tree_files))
        
        # Process each file in the tree
        for path, file_hash in tree_files.items():
            file_path = repo_root / path
            
            # Create parent directories if needed
            os.makedirs(file_path.parent, exist_ok=True)
            
            # Get file content
            _, blob_data = get_object(file_hash, "blob")
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(blob_data)
            
            # Update index
            new_index[path] = {
                'hash': file_hash,
                'size': len(blob_data),
                'mtime': file_path.stat().st_mtime,
            }
            
            progress.update(task, advance=1)
    
    # Update index
    write_index(new_index)

def perform_merge(base_tree, head_tree, branch_tree):
    """Perform a three-way merge between base, head, and branch trees."""
    repo_root = get_repo_root()
    
    # Get all paths from all trees
    all_paths = set(list(base_tree.keys()) + list(head_tree.keys()) + list(branch_tree.keys()))
    
    # Read current index
    index = read_index()
    
    # Track conflicts
    conflicts = []
    
    for path in all_paths:
        base_hash = base_tree.get(path)
        head_hash = head_tree.get(path)
        branch_hash = branch_tree.get(path)
        
        # Case 1: File unchanged in both branches
        if head_hash == branch_hash:
            if head_hash:
                index[path] = {
                    'hash': head_hash,
                    'size': 0,  # Will be updated when writing file
                    'mtime': 0,  # Will be updated when writing file
                }
            continue
        
        # Case 2: File unchanged in one branch
        if head_hash == base_hash:
            # Take the version from branch
            if branch_hash:
                # Get file content
                _, blob_data = get_object(branch_hash, "blob")
                
                # Write file
                file_path = repo_root / path
                os.makedirs(file_path.parent, exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    f.write(blob_data)
                
                # Update index
                index[path] = {
                    'hash': branch_hash,
                    'size': len(blob_data),
                    'mtime': file_path.stat().st_mtime,
                }
            else:
                # File was deleted in branch
                if path in index:
                    del index[path]
                
                file_path = repo_root / path
                if file_path.exists():
                    os.remove(file_path)
            
            continue
        
        if branch_hash == base_hash:
            # Take the version from head
            if head_hash:
                # File already in working directory, no need to update
                index[path] = {
                    'hash': head_hash,
                    'size': 0,  # Will be updated when writing file
                    'mtime': 0,  # Will be updated when writing file
                }
            else:
                # File was deleted in head
                if path in index:
                    del index[path]
                
                file_path = repo_root / path
                if file_path.exists():
                    os.remove(file_path)
            
            continue
        
        # Case 3: File added in one branch but not the other
        if not base_hash:
            if head_hash and not branch_hash:
                # Added in head only, keep it
                continue
            
            if branch_hash and not head_hash:
                # Added in branch only, take it
                _, blob_data = get_object(branch_hash, "blob")
                
                # Write file
                file_path = repo_root / path
                os.makedirs(file_path.parent, exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    f.write(blob_data)
                
                # Update index
                index[path] = {
                    'hash': branch_hash,
                    'size': len(blob_data),
                    'mtime': file_path.stat().st_mtime,
                }
                
                continue
        
        # Case 4: File deleted in one branch but modified in the other
        if not head_hash and base_hash != branch_hash:
            # Deleted in head, modified in branch
            conflicts.append(path)
            continue
        
        if not branch_hash and base_hash != head_hash:
            # Deleted in branch, modified in head
            conflicts.append(path)
            continue
        
        # Case 5: File modified in both branches
        # This is a conflict unless the changes are identical
        if head_hash != branch_hash:
            conflicts.append(path)
    
    # Write updated index
    write_index(index)
    
    return conflicts
