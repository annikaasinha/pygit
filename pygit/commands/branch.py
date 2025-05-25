import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from pygit.utils import (
    get_head_commit, update_ref, get_ref,
    get_branch_name
)
from pygit.config import get_pygit_dir

console = Console()

def branch(name):
    """Create a new branch."""
    try:
        # Get the current HEAD commit
        head_commit = get_head_commit()
        
        if not head_commit:
            console.print("[yellow]Cannot create branch: no commits yet[/yellow]")
            return
        
        # Check if branch already exists
        branch_path = get_pygit_dir() / "refs" / "heads" / name
        
        if branch_path.exists():
            console.print(f"[yellow]Branch '{name}' already exists[/yellow]")
            return
        
        # Create the branch
        update_ref(f"heads/{name}", head_commit)
        
        console.print(f"[green]Created branch '{name}'[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

def list_branches():
    """List all branches."""
    try:
        # Get the current branch
        current_branch = get_branch_name()
        
        # Get all branches
        heads_dir = get_pygit_dir() / "refs" / "heads"
        
        if not heads_dir.exists():
            console.print("[yellow]No branches exist yet[/yellow]")
            return
        
        branches = []
        
        for branch_file in heads_dir.glob("*"):
            if branch_file.is_file():
                branches.append(branch_file.name)
        
        if not branches:
            console.print("[yellow]No branches exist yet[/yellow]")
            return
        
        # Sort branches
        branches.sort()
        
        # Display branches
        table = Table(show_header=False, box=None)
        
        for branch in branches:
            if branch == current_branch:
                table.add_row(f"* [green]{branch}[/green]")
            else:
                table.add_row(f"  {branch}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

def delete_branch(name):
    """Delete a branch."""
    try:
        # Check if branch exists
        branch_path = get_pygit_dir() / "refs" / "heads" / name
        
        if not branch_path.exists():
            console.print(f"[yellow]Branch '{name}' does not exist[/yellow]")
            return
        
        # Check if it's the current branch
        current_branch = get_branch_name()
        
        if name == current_branch:
            console.print(f"[yellow]Cannot delete the currently checked out branch '{name}'[/yellow]")
            return
        
        # Delete the branch
        os.remove(branch_path)
        
        console.print(f"[green]Deleted branch '{name}'[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
