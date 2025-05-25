import os
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from pygit.utils import hash_object, read_index, write_index, is_ignored, logger
from pygit.config import get_repo_root, MAX_OBJECT_SIZE

console = Console()

def add(paths):
    """Add file contents to the index."""
    try:
        repo_root = get_repo_root()
        
        # Read current index
        index = read_index()
        
        # Track all files to add
        all_files = []
        
        # Process each path
        for path_str in paths:
            path = Path(path_str)
            
            if not path.exists():
                console.print(f"[yellow]Warning:[/yellow] '{path}' does not exist, skipping")
                continue
            
            if path.is_dir():
                # Add all files in the directory recursively
                for root, dirs, files in os.walk(path):
                    # Skip .pygit directory
                    if '.pygit' in dirs:
                        dirs.remove('.pygit')
                    
                    # Add each file
                    for file in files:
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(repo_root)
                        
                        # Skip ignored files
                        if is_ignored(str(rel_path)):
                            continue
                        
                        all_files.append(rel_path)
            else:
                # Add single file
                rel_path = path.resolve().relative_to(repo_root)
                
                # Skip ignored files
                if is_ignored(str(rel_path)):
                    continue
                
                all_files.append(rel_path)
        
        # Process files with progress bar
        with Progress() as progress:
            task = progress.add_task("[green]Adding files...", total=len(all_files))
            
            for rel_path in all_files:
                file_path = repo_root / rel_path
                
                try:
                    # Check file size
                    file_size = file_path.stat().st_size
                    if file_size > MAX_OBJECT_SIZE:
                        console.print(f"[yellow]Warning:[/yellow] '{rel_path}' exceeds maximum size ({MAX_OBJECT_SIZE} bytes), skipping")
                        continue
                    
                    # Read file content
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
                    # Hash and store the file content
                    file_hash = hash_object(data)
                    
                    # Update index
                    index[str(rel_path)] = {
                        'hash': file_hash,
                        'size': file_size,
                        'mtime': file_path.stat().st_mtime,
                    }
                    
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Error adding '{rel_path}': {str(e)}")
                
                progress.update(task, advance=1)
        
        # Write updated index
        write_index(index)
        
        console.print(f"[green]Added {len(all_files)} files to the index[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
