import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from pygit.utils import (
    get_head_commit, get_commit_info, 
    format_timestamp, get_branch_name
)

console = Console()

def log(oneline=False, graph=False, max_count=None):
    """Show commit logs."""
    try:
        # Get the current HEAD commit
        head_commit = get_head_commit()
        
        if not head_commit:
            console.print("[yellow]No commits yet[/yellow]")
            return
        
        # Get branch name
        branch_name = get_branch_name()
        
        # Traverse the commit history
        commits = []
        visited = set()
        
        def traverse_commits(commit_hash, branch=None, depth=0):
            if not commit_hash or commit_hash in visited or (max_count and len(commits) >= max_count):
                return
            
            visited.add(commit_hash)
            
            try:
                commit_info = get_commit_info(commit_hash)
                commit_info['depth'] = depth
                commit_info['branch'] = branch
                commits.append(commit_info)
                
                # Traverse parents
                for parent in commit_info.get('parents', []):
                    traverse_commits(parent, branch, depth + 1)
            except Exception as e:
                console.print(f"[yellow]Warning: Error processing commit {commit_hash}: {str(e)}[/yellow]")
        
        # Start traversal from HEAD
        traverse_commits(head_commit, branch_name)
        
        # Sort commits by depth
        commits.sort(key=lambda c: c['depth'])
        
        # Limit number of commits if requested
        if max_count:
            commits = commits[:max_count]
        
        # Display commits
        if oneline:
            # One line per commit
            for commit in commits:
                hash_short = commit['hash'][:7]
                message_first_line = commit.get('message', '').split('\n')[0]
                console.print(f"[yellow]{hash_short}[/yellow] {message_first_line}")
        
        elif graph:
            # TODO: Implement ASCII graph
            console.print("[yellow]Graph display not yet implemented[/yellow]")
            
            # Fall back to regular display
            for commit in commits:
                hash_value = commit['hash']
                author = commit.get('author', 'Unknown')
                message = commit.get('message', '')
                
                # Format author line
                author_parts = author.split('>')
                if len(author_parts) > 1:
                    author_name = author_parts[0] + '>'
                    timestamp = author_parts[1].strip()
                    author_line = f"{author_name} {format_timestamp(timestamp)}"
                else:
                    author_line = author
                
                # Create panel for commit
                text = Text()
                text.append(f"commit {hash_value}\n", style="yellow")
                text.append(f"Author: {author_line}\n\n")
                text.append(message)
                
                console.print(Panel(text, expand=False))
                console.print()
        
        else:
            # Regular display
            for commit in commits:
                hash_value = commit['hash']
                author = commit.get('author', 'Unknown')
                message = commit.get('message', '')
                
                # Format author line
                author_parts = author.split('>')
                if len(author_parts) > 1:
                    author_name = author_parts[0] + '>'
                    timestamp = author_parts[1].strip()
                    author_line = f"{author_name} {format_timestamp(timestamp)}"
                else:
                    author_line = author
                
                console.print(f"[yellow]commit {hash_value}[/yellow]")
                console.print(f"Author: {author_line}")
                console.print()
                console.print(f"    {message}")
                console.print()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
