#!/usr/bin/env python3
import os
import sys
import click
from rich.console import Console
from rich.traceback import install

from pygit.commands.init import init
from pygit.commands.add import add
from pygit.commands.commit import commit
from pygit.commands.status import status
from pygit.commands.log import log
from pygit.commands.diff import diff
from pygit.commands.branch import branch, list_branches
from pygit.commands.checkout import checkout
from pygit.commands.merge import merge
from pygit.security import verify_repo_security

# Install rich traceback handler
install()
console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PyGit - A Git-like version control system implemented in Python."""
    pass

@cli.command()
@click.option("--path", default=".", help="Path where to initialize the repository")
def init(path):
    """Initialize a new PyGit repository."""
    from pygit.commands.init import init as init_cmd
    init_cmd(path)

@cli.command()
@click.argument("paths", nargs=-1, required=True)
def add(paths):
    """Add file contents to the index."""
    from pygit.commands.add import add as add_cmd
    add_cmd(paths)

@cli.command()
@click.option("-m", "--message", required=True, help="Commit message")
@click.option("--author", help="Author of the commit (format: Name <email>)")
def commit(message, author):
    """Record changes to the repository."""
    from pygit.commands.commit import commit as commit_cmd
    commit_cmd(message, author)

@cli.command()
def status():
    """Show the working tree status."""
    from pygit.commands.status import status as status_cmd
    status_cmd()

@cli.command()
@click.option("--oneline", is_flag=True, help="Show each commit on a single line")
@click.option("--graph", is_flag=True, help="Show ASCII graph of branch and merge history")
@click.option("-n", "--max-count", type=int, help="Limit the number of commits to show")
def log(oneline, graph, max_count):
    """Show commit logs."""
    from pygit.commands.log import log as log_cmd
    log_cmd(oneline, graph, max_count)

@cli.command()
@click.argument("path", required=False)
@click.option("--staged", is_flag=True, help="Show diff between index and HEAD")
def diff(path, staged):
    """Show changes between commits, commit and working tree, etc."""
    from pygit.commands.diff import diff as diff_cmd
    diff_cmd(path, staged)

@cli.command()
@click.argument("name", required=False)
@click.option("-l", "--list", "list_all", is_flag=True, help="List all branches")
def branch(name, list_all):
    """List, create, or delete branches."""
    from pygit.commands.branch import branch as branch_cmd, list_branches
    if list_all:
        list_branches()
    elif name:
        branch_cmd(name)
    else:
        list_branches()

@cli.command()
@click.argument("branch_name", required=True)
def checkout(branch_name):
    """Switch branches or restore working tree files."""
    from pygit.commands.checkout import checkout as checkout_cmd
    checkout_cmd(branch_name)

@cli.command()
@click.argument("branch_name", required=True)
@click.option("--no-ff", is_flag=True, help="Create a merge commit even when fast-forward is possible")
def merge(branch_name, no_ff):
    """Join two or more development histories together."""
    from pygit.commands.merge import merge as merge_cmd
    merge_cmd(branch_name, no_ff)

@cli.command()
def security():
    """Check repository for security issues."""
    from pygit.security import verify_repo_security
    verify_repo_security()

def main():
    try:
        # Verify repository security before executing commands
        # (except for init which creates a new repo)
        if len(sys.argv) > 1 and sys.argv[1] != "init" and sys.argv[1] != "security":
            verify_repo_security()
        cli()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
