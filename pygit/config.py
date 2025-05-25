import os
from pathlib import Path

# Repository structure
PYGIT_DIR = ".pygit"
OBJECTS_DIR = os.path.join(PYGIT_DIR, "objects")
REFS_DIR = os.path.join(PYGIT_DIR, "refs")
HEADS_DIR = os.path.join(REFS_DIR, "heads")
TAGS_DIR = os.path.join(REFS_DIR, "tags")
HEAD_FILE = os.path.join(PYGIT_DIR, "HEAD")
INDEX_FILE = os.path.join(PYGIT_DIR, "index")
CONFIG_FILE = os.path.join(PYGIT_DIR, "config")
EXCLUDE_FILE = os.path.join(PYGIT_DIR, "info", "exclude")

# Default branch name
DEFAULT_BRANCH = "master"

# Security settings
MAX_OBJECT_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_HASH_ALGORITHMS = ["sha1", "sha256"]
DEFAULT_HASH_ALGORITHM = "sha256"  # More secure than SHA-1
SECURE_PERMISSIONS = 0o700  # rwx------

def get_pygit_dir(path="."):
    """Get the .pygit directory from the given path or its parents."""
    path = Path(path).resolve()
    
    while path != Path('/'):
        pygit_path = path / PYGIT_DIR
        if pygit_path.exists():
            return pygit_path
        path = path.parent
    
    raise ValueError("Not a PyGit repository (or any parent directory)")

def get_repo_root(path="."):
    """Get the repository root directory."""
    return get_pygit_dir(path).parent
