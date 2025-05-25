import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from pygit.utils import (
    read_index, hash_object, get_head_commit, 
    read_tree, get_branch_name, is_ignored
)
from pygit.config import get_repo_root

console = Console()

def status():
    """Show the working tree status."""
    try:
        repo_root = get_repo_root()
        branch_name = get_branch_name()
        
        console.print(f"On branch [bold]{branch_name}[/bold]")
        
        # Read the index
        index = read_index()
        
        # Get the current HEAD commit and its tree
        head_commit = get_head_commit()
        head_tree = {}
        
        if head_commit:
            from pygit.utils import get_commit_info
            commit_info = get_commit_info(head_commit)
            head_tree = read_tree(commit_info["tree"])
        
        # Check for changes
        staged_new = []
        staged_modified = []
        staged_deleted = []
        unstaged_modified = []
        unstaged_deleted = []
        untracked = []
        
        # Check indexed files against HEAD
        for path, entry in index.items():
            if path in head_tree:
                if entry['hash'] != head_tree[path]:
                    staged_modified.append(path)
            else:
                staged_new.append(path)
        
        # Check for files in HEAD but not in index
        for path in head_tree:
            if path not in index:
                staged_deleted.append(path)
        
        # Check working directory against index
        for path, entry in index.items():
            file_path = repo_root / path
            
            if not file_path.exists():
                unstaged_deleted.append(path)
            else:
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                file_hash = hash_object(data, write=False)
                
                if file_hash != entry['hash']:
                    unstaged_modified.append(path)
        
        # Check for untracked files
        for root, dirs, files in os.walk(repo_root):
            # Skip .pygit directory
            if '.pygit' in dirs:
                dirs.remove('.pygit')
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_root)
                path_str = str(rel_path)
                
                # Skip ignored files
                if is_ignored(path_str):
                    continue
                
                if path_str not in index:
                    untracked.append(path_str)
        
        # Print status
        if not head_commit:
            console.print("No commits yet")
        
        if not (staged_new or staged_modified or staged_deleted or 
                unstaged_modified or unstaged_deleted or untracked):
            console.print("[green]Working tree clean[/green]")
            return
        
        # Changes to be committed
        if staged_new or staged_modified or staged_deleted:
            console.print("\n[green]Changes to be committed:[/green]")
            table = Table(show_header=False, box=None)
            
            for path in sorted(staged_new):
                table.add_row("  new file:   " + path, style="green")
            
            for path in sorted(staged_modified):
                table.add_row("  modified:   " + path, style="green")
            
            for path in sorted(staged_deleted):
                table.add_row("  deleted:    " + path, style="green")
            
            console.print(table)
        
        # Changes not staged for commit
        if unstaged_modified or unstaged_deleted:
            console.print("\n[red]Changes not staged for commit:[/red]")
            table = Table(show_header=False, box=None)
            
            for path in sorted(unstaged_modified):
                table.add_row("  modified:   " + path, style="red")
            
            for path in sorted(unstaged_deleted):
                table.add_row("  deleted:    " + path, style="red")
            
            console.print(table)
        
        # Untracked files
        if untracked:
            console.print("\n[red]Untracked files:[/red]")
            table = Table(show_header=False, box=None)
            
            for path in sorted(untracked):
                table.add_row("  " + path, style="red")
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
