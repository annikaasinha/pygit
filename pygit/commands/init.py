import os
import sys
from pathlib import Path
from rich.console import Console

from pygit.config import (
    PYGIT_DIR, OBJECTS_DIR, REFS_DIR, HEADS_DIR, 
    TAGS_DIR, HEAD_FILE, INDEX_FILE, CONFIG_FILE,
    DEFAULT_BRANCH, SECURE_PERMISSIONS
)
from pygit.utils import logger

console = Console()

def init(path="."):
    """Initialize a new PyGit repository."""
    repo_path = Path(path).resolve()
    pygit_dir = repo_path / PYGIT_DIR
    
    # Check if repository already exists
    if pygit_dir.exists():
        console.print(f"[yellow]Repository already initialized in {repo_path}[/yellow]")
        return
    
    try:
        # Create directory structure
        os.makedirs(pygit_dir, mode=SECURE_PERMISSIONS)
        os.makedirs(pygit_dir / "objects", mode=SECURE_PERMISSIONS)
        os.makedirs(pygit_dir / "refs" / "heads", mode=SECURE_PERMISSIONS)
        os.makedirs(pygit_dir / "refs" / "tags", mode=SECURE_PERMISSIONS)
        os.makedirs(pygit_dir / "info", mode=SECURE_PERMISSIONS)
        os.makedirs(pygit_dir / "hooks", mode=SECURE_PERMISSIONS)
        
        # Initialize HEAD to point to master branch
        with open(pygit_dir / "HEAD", 'w') as f:
            f.write(f"ref: refs/heads/{DEFAULT_BRANCH}\n")
        
        # Create empty index file
        with open(pygit_dir / "index", 'wb') as f:
            import pickle
            pickle.dump({}, f)
        
        # Create basic configuration
        with open(pygit_dir / "config", 'w') as f:
            f.write("""[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
[user]
    name = 
    email = 
[pygit]
    hash = sha256
""")
        
        # Create .pygitignore template
        with open(pygit_dir / "info" / "exclude", 'w') as f:
            f.write("""# Ignore patterns for PyGit
# Lines starting with '#' are comments
# Empty lines are ignored
# Standard glob patterns work:
#   * matches anything except /
#   ? matches any single character
#   [abc] matches any character inside the brackets
#   ** matches nested directories

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
Thumbs.db
""")
        
        # Set secure permissions for all files
        for root, dirs, files in os.walk(pygit_dir):
            for d in dirs:
                os.chmod(os.path.join(root, d), SECURE_PERMISSIONS)
            for f in files:
                os.chmod(os.path.join(root, f), SECURE_PERMISSIONS)
        
        console.print(f"[green]Initialized empty PyGit repository in {repo_path / PYGIT_DIR}[/green]")
        
        # Suggest next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Configure your user information:")
        console.print("     $ git config --global user.name \"Your Name\"")
        console.print("     $ git config --global user.email \"your.email@example.com\"")
        console.print("  2. Add some files to the repository:")
        console.print("     $ pygit add .")
        console.print("  3. Create your first commit:")
        console.print("     $ pygit commit -m \"Initial commit\"")
        
    except Exception as e:
        console.print(f"[bold red]Error initializing repository:[/bold red] {str(e)}")
        # Clean up if initialization failed
        if pygit_dir.exists():
            import shutil
            shutil.rmtree(pygit_dir)
        sys.exit(1)
