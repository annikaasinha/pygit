import os
import stat
import re
import hashlib
from pathlib import Path
from typing import List, Set

from pygit.config import get_pygit_dir, SECURE_PERMISSIONS
from pygit.utils import logger

def verify_repo_security():
    """Verify repository security and fix any issues."""
    try:
        pygit_dir = get_pygit_dir()
    except ValueError:
        # Not in a repository, nothing to check
        return
    
    issues = []
    
    # Check directory permissions
    issues.extend(check_directory_permissions(pygit_dir))
    
    # Check for suspicious files
    issues.extend(check_suspicious_files(pygit_dir))
    
    # Check for large objects
    issues.extend(check_large_objects(pygit_dir))
    
    # Report issues
    if issues:
        logger.warning(f"Found {len(issues)} security issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        logger.info("Run 'pygit security --fix' to automatically fix these issues")
    else:
        logger.info("Repository security check passed")

def check_directory_permissions(pygit_dir: Path) -> List[str]:
    """Check directory permissions for security issues."""
    issues = []
    
    # Check .pygit directory permissions
    mode = pygit_dir.stat().st_mode
    if mode & 0o077:  # Check if group or others have any permissions
        issues.append(f"{pygit_dir} has insecure permissions: {mode & 0o777:o}")
    
    # Check permissions of important subdirectories
    for subdir in ["objects", "refs"]:
        path = pygit_dir / subdir
        if path.exists():
            mode = path.stat().st_mode
            if mode & 0o077:
                issues.append(f"{path} has insecure permissions: {mode & 0o777:o}")
    
    return issues

def check_suspicious_files(pygit_dir: Path) -> List[str]:
    """Check for suspicious files in the repository."""
    issues = []
    
    # Patterns for potentially malicious files
    suspicious_patterns = [
        r'.*\.exe$',
        r'.*\.dll$',
        r'.*\.so$',
        r'.*\.sh$',
        r'.*\.bat$',
        r'.*\.cmd$',
        r'.*\.ps1$',
    ]
    
    # Compile patterns
    patterns = [re.compile(pattern) for pattern in suspicious_patterns]
    
    # Walk through the objects directory
    objects_dir = pygit_dir / "objects"
    if objects_dir.exists():
        for root, _, files in os.walk(objects_dir):
            for file in files:
                file_path = Path(root) / file
                
                # Check file content for suspicious patterns
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read(1024)  # Read first 1KB
                    
                    # Check for executable content
                    if b'MZ' in content or b'ELF' in content:
                        issues.append(f"Suspicious executable content in {file_path}")
                except Exception:
                    pass
    
    return issues

def check_large_objects(pygit_dir: Path) -> List[str]:
    """Check for unusually large objects that might indicate abuse."""
    issues = []
    large_size = 50 * 1024 * 1024  # 50MB
    
    # Walk through the objects directory
    objects_dir = pygit_dir / "objects"
    if objects_dir.exists():
        for root, _, files in os.walk(objects_dir):
            for file in files:
                file_path = Path(root) / file
                
                # Check file size
                try:
                    size = file_path.stat().st_size
                    if size > large_size:
                        issues.append(f"Unusually large object: {file_path} ({size // 1024 // 1024}MB)")
                except Exception:
                    pass
    
    return issues

def fix_security_issues(pygit_dir: Path) -> None:
    """Fix security issues in the repository."""
    # Fix directory permissions
    for root, dirs, files in os.walk(pygit_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), SECURE_PERMISSIONS)
        for f in files:
            os.chmod(os.path.join(root, f), SECURE_PERMISSIONS)
    
    logger.info("Fixed directory and file permissions")

def validate_hash(hash_value: str) -> bool:
    """Validate that a hash is in the correct format."""
    return bool(re.match(r'^[0-9a-f]{40,64}$', hash_value))

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent command injection."""
    # Remove any shell metacharacters
    return re.sub(r'[;&|<>$`\\"\']', '', input_str)
