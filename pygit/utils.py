import os
import hashlib
import json
import pickle
import zlib
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import shutil

from pygit.config import (
    get_pygit_dir, get_repo_root, PYGIT_DIR, OBJECTS_DIR, 
    REFS_DIR, HEADS_DIR, HEAD_FILE, INDEX_FILE, DEFAULT_HASH_ALGORITHM,
    MAX_OBJECT_SIZE, SECURE_PERMISSIONS
)

def init_logger():
    """Initialize logging for PyGit."""
    import logging
    from rich.logging import RichHandler
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    
    return logging.getLogger("pygit")

logger = init_logger()

def hash_object(data: bytes, obj_type: str = "blob", write: bool = True) -> str:
    """
    Hash an object with the configured hash algorithm and optionally store it.
    Returns the hash.
    """
    # Security check for large objects
    if len(data) > MAX_OBJECT_SIZE:
        raise ValueError(f"Object size exceeds maximum allowed size ({MAX_OBJECT_SIZE} bytes)")
    
    # Prepare header (similar to Git's format)
    header = f"{obj_type} {len(data)}\0".encode()
    store = header + data
    
    # Calculate hash
    hash_obj = hashlib.new(DEFAULT_HASH_ALGORITHM)
    hash_obj.update(store)
    hash_value = hash_obj.hexdigest()
    
    # Store the object if requested
    if write:
        repo_path = get_pygit_dir()
        obj_dir = repo_path / "objects" / hash_value[:2]
        obj_path = obj_dir / hash_value[2:]
        
        if not obj_path.exists():
            obj_dir.mkdir(exist_ok=True, parents=True)
            
            # Compress the data before storing
            compressed_data = zlib.compress(store)
            
            # Write with secure permissions
            with open(obj_path, 'wb') as f:
                f.write(compressed_data)
            
            # Set secure permissions
            os.chmod(obj_path, SECURE_PERMISSIONS)
    
    return hash_value

def get_object(hash_value: str, expected_type: Optional[str] = None) -> Tuple[str, bytes]:
    """
    Retrieve an object from the objects directory by its hash.
    Returns (object_type, data).
    """
    # Validate hash format
    if not re.match(r'^[0-9a-f]{40,64}$', hash_value):
        raise ValueError(f"Invalid hash format: {hash_value}")
    
    repo_path = get_pygit_dir()
    obj_path = repo_path / "objects" / hash_value[:2] / hash_value[2:]
    
    if not obj_path.exists():
        raise ValueError(f"Object {hash_value} not found")
    
    try:
        with open(obj_path, 'rb') as f:
            compressed_content = f.read()
        
        # Decompress the content
        content = zlib.decompress(compressed_content)
        
        # Parse the header
        null_pos = content.find(b'\0')
        if null_pos == -1:
            raise ValueError(f"Invalid object format: {hash_value}")
        
        header = content[:null_pos].decode()
        header_parts = header.split()
        
        if len(header_parts) < 2:
            raise ValueError(f"Invalid object header: {header}")
        
        obj_type = header_parts[0]
        
        # Verify the type if expected_type is provided
        if expected_type and obj_type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {obj_type}")
        
        # Return the object data
        return obj_type, content[null_pos+1:]
    
    except Exception as e:
        logger.error(f"Error reading object {hash_value}: {str(e)}")
        raise

def read_index() -> Dict[str, Dict[str, Any]]:
    """Read the index file and return its contents as a dictionary."""
    index_path = get_pygit_dir() / "index"
    
    if not index_path.exists():
        return {}
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        # Validate index structure
        if not isinstance(index_data, dict):
            logger.warning("Invalid index format, resetting index")
            return {}
        
        return index_data
    except Exception as e:
        logger.error(f"Error reading index: {str(e)}")
        return {}

def write_index(index_data: Dict[str, Dict[str, Any]]) -> None:
    """Write the index data to the index file."""
    index_path = get_pygit_dir() / "index"
    
    try:
        # Create a temporary file first
        temp_path = index_path.with_suffix('.tmp')
        with open(temp_path, 'wb') as f:
            pickle.dump(index_data, f)
        
        # Set secure permissions
        os.chmod(temp_path, SECURE_PERMISSIONS)
        
        # Rename to the actual index file (atomic operation)
        shutil.move(temp_path, index_path)
    except Exception as e:
        logger.error(f"Error writing index: {str(e)}")
        raise

def get_head_commit() -> Optional[str]:
    """Get the current HEAD commit hash."""
    try:
        head_file = get_pygit_dir() / "HEAD"
        
        if not head_file.exists():
            return None
        
        with open(head_file, 'r') as f:
            head_ref = f.read().strip()
        
        if head_ref.startswith('ref: '):
            ref_path = get_pygit_dir() / head_ref[5:]
            if not ref_path.exists():
                return None
            
            with open(ref_path, 'r') as f:
                return f.read().strip()
        
        # Detached HEAD
        return head_ref
    except Exception as e:
        logger.error(f"Error getting HEAD commit: {str(e)}")
        return None

def update_ref(ref_name: str, hash_value: str) -> None:
    """Update a reference to point to a specific hash."""
    if not ref_name.startswith('refs/'):
        ref_name = f"refs/{ref_name}"
    
    ref_path = get_pygit_dir() / ref_name
    ref_dir = ref_path.parent
    
    # Create directory if it doesn't exist
    if not ref_dir.exists():
        ref_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(ref_dir, SECURE_PERMISSIONS)
    
    # Write the reference
    with open(ref_path, 'w') as f:
        f.write(f"{hash_value}\n")
    
    # Set secure permissions
    os.chmod(ref_path, SECURE_PERMISSIONS)

def get_ref(ref_name: str) -> Optional[str]:
    """Get the hash that a reference points to."""
    if not ref_name.startswith('refs/'):
        ref_name = f"refs/{ref_name}"
    
    ref_path = get_pygit_dir() / ref_name
    
    if not ref_path.exists():
        return None
    
    with open(ref_path, 'r') as f:
        return f.read().strip()

def get_branch_name() -> str:
    """Get the name of the current branch."""
    head_file = get_pygit_dir() / "HEAD"
    
    if not head_file.exists():
        return "No branch"
    
    with open(head_file, 'r') as f:
        head_ref = f.read().strip()
    
    if head_ref.startswith('ref: refs/heads/'):
        return head_ref[16:]  # Remove 'ref: refs/heads/'
    
    # Detached HEAD
    return "HEAD detached"

def create_tree_from_index(index_data: Dict[str, Dict[str, Any]]) -> str:
    """Create a tree object from the index data."""
    # Sort entries by path
    sorted_entries = sorted(index_data.items())
    
    # Build tree structure
    root_tree = {}
    
    for path, entry in sorted_entries:
        parts = path.split('/')
        current = root_tree
        
        # Navigate to the correct subtree
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Add the file entry
        current[parts[-1]] = entry['hash']
    
    # Recursively create tree objects
    return create_tree_object(root_tree)

def create_tree_object(tree_dict: Dict[str, Union[str, Dict]]) -> str:
    """Recursively create tree objects from a dictionary structure."""
    tree_entries = []
    
    for name, value in sorted(tree_dict.items()):
        if isinstance(value, dict):
            # This is a subtree
            subtree_hash = create_tree_object(value)
            tree_entries.append(f"tree {subtree_hash} {name}")
        else:
            # This is a blob
            tree_entries.append(f"blob {value} {name}")
    
    tree_content = "\n".join(tree_entries).encode()
    return hash_object(tree_content, "tree")

def read_tree(tree_hash: str, prefix: str = "") -> Dict[str, str]:
    """Read a tree object and return a dictionary mapping paths to hashes."""
    result = {}
    
    _, tree_data = get_object(tree_hash, "tree")
    if not tree_data:
        return result
    
    for line in tree_data.decode().splitlines():
        if not line:
            continue
        
        obj_type, obj_hash, name = line.split(" ", 2)
        path = os.path.join(prefix, name)
        
        if obj_type == "blob":
            result[path] = obj_hash
        elif obj_type == "tree":
            # Recursively read subtree
            subtree = read_tree(obj_hash, path)
            result.update(subtree)
    
    return result

def get_commit_info(commit_hash: str) -> Dict[str, Any]:
    """Get information about a commit."""
    _, commit_data = get_object(commit_hash, "commit")
    lines = commit_data.decode().splitlines()
    
    commit_info = {
        "hash": commit_hash,
        "parents": [],
    }
    
    # Parse header
    i = 0
    while i < len(lines) and lines[i]:
        line = lines[i]
        if line.startswith("tree "):
            commit_info["tree"] = line[5:]
        elif line.startswith("parent "):
            commit_info["parents"].append(line[7:])
        elif line.startswith("author "):
            commit_info["author"] = line[7:]
        elif line.startswith("committer "):
            commit_info["committer"] = line[10:]
        i += 1
    
    # Parse message
    if i < len(lines):
        commit_info["message"] = "\n".join(lines[i+1:])
    
    return commit_info

def format_timestamp(timestamp_str: str) -> str:
    """Format a timestamp string for display."""
    try:
        # Parse timestamp (Unix timestamp with timezone)
        parts = timestamp_str.split()
        timestamp = int(parts[0])
        timezone = parts[1]
        
        # Convert to datetime
        dt = datetime.fromtimestamp(timestamp)
        
        # Format for display
        return dt.strftime("%a %b %d %H:%M:%S %Y") + f" {timezone}"
    except Exception:
        return timestamp_str

def is_ignored(path: str) -> bool:
    """Check if a path should be ignored based on .pygitignore rules."""
    # TODO: Implement .pygitignore parsing
    return False
