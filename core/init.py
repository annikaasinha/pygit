import os
from pathlib import Path

def initialize_repo(path='.'):
    """
    Initialize a new mygit repository at the specified path
    """
    mygit_dir = Path(path) / '.mygit'
    
    # Check if repository already exists
    if mygit_dir.exists():
        print(f"Repository already initialized in {os.path.abspath(path)}")
        return False
    
    # Create directory structure
    (mygit_dir / 'objects').mkdir(parents=True)
    (mygit_dir / 'refs' / 'heads').mkdir(parents=True)
    
    # Initialize HEAD to point to master branch
    with open(mygit_dir / 'HEAD', 'w') as f:
        f.write('ref: refs/heads/master\n')
    
    # Create empty index file
    with open(mygit_dir / 'index', 'w') as f:
        f.write('')
    
    print(f"Initialized empty mygit repository in {os.path.abspath(path)}/{mygit_dir}")
    return True

# This allows the module to be run directly
if __name__ == "__main__":
    initialize_repo()
