import os
import sys
import time
from pathlib import Path
from rich.console import Console

from pygit.utils import (
    read_index, hash_object, get_head_commit, 
    create_tree_from_index, update_ref, get_branch_name
)
from pygit.config import get_repo_root

console = Console()

def commit(message, author=None):
    """Record changes to the repository."""
    try:
        # Read the index
        index = read_index()
        
        if not index:
            console.print("[yellow]Nothing to commit (empty index)[/yellow]")
            return
        
        # Get user information
        if not author:
            # Try to get from environment variables or config
            import os
            name = os.environ.get("GIT_AUTHOR_NAME", "Unknown")
            email = os.environ.get("GIT_AUTHOR_EMAIL", "unknown@example.com")
            author = f"{name} <{email}>"
        
        # Create a tree object from the index
        tree_hash = create_tree_from_index(index)
        
        # Get the current HEAD commit
        parent = get_head_commit()
        
        # Create the commit object
        commit_content = f"tree {tree_hash}\n"
        
        if parent:
            commit_content += f"parent {parent}\n"
        
        timestamp = int(time.time())
        timezone = time.strftime("%z")
        
        commit_content += f"author {author} {timestamp} {timezone}\n"
        commit_content += f"committer {author} {timestamp} {timezone}\n\n"
        commit_content += message + "\n"
        
        # Hash and store the commit
        commit_hash = hash_object(commit_content.encode(), "commit")
        
        # Update the current branch reference
        branch_name = get_branch_name()
        if branch_name != "HEAD detached":
            update_ref(f"heads/{branch_name}", commit_hash)
        else:
            # Update HEAD directly (detached HEAD state)
            head_file = get_repo_root() / ".pygit" / "HEAD"
            with open(head_file, 'w') as f:
                f.write(commit_hash + "\n")
        
        # Print commit information
        console.print(f"[green][{branch_name} {commit_hash[:7]}] {message}[/green]")
        
        # Show stats
        changed_files = len(index)
        console.print(f"[green]{changed_files} files changed[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
