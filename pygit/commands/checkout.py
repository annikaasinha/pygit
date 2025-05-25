import os
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from pygit.utils import (
    get_head_commit, get_ref, read_index, write_index,
    read_tree, get_object, get_commit_info
)
from pygit.config import get_pygit_dir, get_repo_root

console = Console()

def checkout(branch_name):
    """Switch branches or restore working tree files."""
    try:
        pygit_dir = get_pygit_dir()
        repo_root = get_repo_root()
        
        # Check if branch exists
        branch_path = pygit_dir / "refs" / "heads" / branch_name
        
        if not branch_path.exists():
            # Check if it's a commit hash
            if len(branch_name) >= 4 and all(c in "0123456789abcdef" for c in branch_name.lower()):
                # Try to find the commit
                try:
                    commit_info = get_commit_info(branch_name)
                    console.print(f"[yellow]Note: checking out '{branch_name}'.[/yellow]")
                    console.print("[yellow]You are in 'detached HEAD' state.[/yellow]")
                    
                    # Update HEAD to point directly to the commit
                    with open(pygit_dir / "HEAD", 'w') as f:
                        f.write(branch_name)
                    
                    # Update working directory
                    update_working_directory(commit_info["tree"])
                    return
                except Exception:
                    pass
            
            console.print(f"[yellow]Branch '{branch_name}' does not exist[/yellow]")
            return
        
        # Get the current branch
        current_branch = None
        head_file = pygit_dir / "HEAD"
        
        with open(head_file, 'r') as f:
            head_ref = f.read().strip()
        
        if head_ref.startswith('ref: refs/heads/'):
            current_branch = head_ref[16:]
        
        # Don't do anything if we're already on this branch
        if current_branch == branch_name:
            console.print(f"[yellow]Already on branch '{branch_name}'[/yellow]")
            return
        
        # Get the commit that the branch points to
        with open(branch_path, 'r') as f:
            branch_commit = f.read().strip()
        
        # Update HEAD to point to the branch
        with open(head_file, 'w') as f:
            f.write(f"ref: refs/heads/{branch_name}")
        
        # Get the tree from the commit
        commit_info = get_commit_info(branch_commit)
        tree_hash = commit_info["tree"]
        
        # Update working directory
        update_working_directory(tree_hash)
        
        console.print(f"[green]Switched to branch '{branch_name}'[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

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
