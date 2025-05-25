import sys
import difflib
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

from pygit.utils import (
    read_index, get_head_commit, get_commit_info,
    read_tree, get_object
)
from pygit.config import get_repo_root

console = Console()

def diff(path=None, staged=False):
    """Show changes between commits, commit and working tree, etc."""
    try:
        repo_root = get_repo_root()
        
        # Read the index
        index = read_index()
        
        # Get the current HEAD commit and its tree
        head_commit = get_head_commit()
        head_tree = {}
        
        if head_commit:
            commit_info = get_commit_info(head_commit)
            head_tree = read_tree(commit_info["tree"])
        
        # Determine which files to diff
        files_to_diff = []
        
        if path:
            # Diff a specific file or directory
            target_path = Path(path)
            
            if target_path.is_dir():
                # Find all files in the directory
                for file_path in index:
                    if Path(file_path).is_relative_to(target_path):
                        files_to_diff.append(file_path)
            else:
                # Single file
                rel_path = str(target_path.relative_to(repo_root))
                if rel_path in index or rel_path in head_tree:
                    files_to_diff.append(rel_path)
        else:
            # Diff all files
            all_paths = set(list(index.keys()) + list(head_tree.keys()))
            files_to_diff = sorted(all_paths)
        
        # Process each file
        for file_path in files_to_diff:
            file_on_disk = repo_root / file_path
            
            # Get file content from different sources
            head_content = None
            index_content = None
            disk_content = None
            
            # Get content from HEAD
            if file_path in head_tree:
                try:
                    _, blob_data = get_object(head_tree[file_path], "blob")
                    head_content = blob_data.decode(errors='replace').splitlines()
                except Exception:
                    head_content = []
            
            # Get content from index
            if file_path in index:
                try:
                    _, blob_data = get_object(index['hash'], "blob")
                    index_content = blob_data.decode(errors='replace').splitlines()
                except Exception:
                    index_content = []
            
            # Get content from disk
            if file_on_disk.exists():
                try:
                    with open(file_on_disk, 'r', errors='replace') as f:
                        disk_content = f.read().splitlines()
                except Exception:
                    disk_content = []
            
            # Determine which diff to show
            if staged:
                # Diff between HEAD and index
                if head_content is not None and index_content is not None:
                    show_diff(file_path, head_content, index_content, "HEAD", "index")
            else:
                # Diff between index (or HEAD if not in index) and working directory
                if file_path in index:
                    if index_content is not None and disk_content is not None:
                        show_diff(file_path, index_content, disk_content, "index", "working tree")
                elif head_content is not None and disk_content is not None:
                    show_diff(file_path, head_content, disk_content, "HEAD", "working tree")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

def show_diff(file_path, a_lines, b_lines, a_label, b_label):
    """Show the diff between two versions of a file."""
    console.print(f"[bold]diff --git a/{file_path} b/{file_path}[/bold]")
    console.print(f"[bold]--- a/{file_path} ({a_label})[/bold]")
    console.print(f"[bold]+++ b/{file_path} ({b_label})[/bold]")
    
    # Generate unified diff
    diff = list(difflib.unified_diff(
        a_lines, b_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm='',
        n=3
    ))
    
    # Skip the first two lines (already printed above)
    if len(diff) > 2:
        diff_text = "\n".join(diff[2:])
        
        # Use rich's Syntax for highlighting
        syntax = Syntax(diff_text, "diff", theme="ansi_dark", line_numbers=False)
        console.print(syntax)
        console.print()
