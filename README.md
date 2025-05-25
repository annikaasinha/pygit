# PyGit: A Git-like Version Control System in Python

PyGit is a Python implementation of a Git-like version control system. It's designed to help you understand how Git works internally by implementing the core functionality in a clean, well-documented Python codebase.

## Features

- Core Git functionality: `init`, `add`, `commit`, `log`, `status`, `diff`, `branch`, `checkout`, `merge`
- Content-addressable storage using SHA-256 hashing
- Merkle tree structure for tracking file changes
- Branch management and merging capabilities
- Security features to protect against common vulnerabilities

## Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/yourusername/pygit.git
cd pygit

# Install the package
pip install -e .
\`\`\`

## Usage

\`\`\`bash
# Initialize a new repository
pygit init

# Add files to the index
pygit add file.txt

# Commit changes
pygit commit -m "Initial commit"

# Show commit history
pygit log

# Show repository status
pygit status

# Create a new branch
pygit branch feature

# Switch to a branch
pygit checkout feature

# Merge branches
pygit merge feature
\`\`\`

## Security Features

PyGit includes several security features:

- Secure file permissions for repository data
- Input validation to prevent command injection
- Size limits on objects to prevent denial of service
- Detection of suspicious files and executables
- Repository security verification

## Project Structure

\`\`\`
pygit/
├── __init__.py         # Package initialization
├── cli.py              # Command-line interface
├── config.py           # Configuration settings
├── utils.py            # Utility functions
├── security.py         # Security features
└── commands/           # Command implementations
    ├── __init__.py
    ├── init.py         # Initialize repository
    ├── add.py          # Add files to index
    ├── commit.py       # Commit changes
    ├── status.py       # Show status
    ├── log.py          # Show commit history
    ├── diff.py         # Show differences
    ├── branch.py       # Branch management
    ├── checkout.py     # Switch branches
    └── merge.py        # Merge branches
\`\`\`

## Understanding Git Internals

This project helps you understand several key Git concepts:

1. **Content-addressable storage**: How Git uses hashes to store and retrieve objects
2. **Merkle trees**: How Git creates a tree structure representing the repository state
3. **Branching and merging**: How Git tracks different development lines
4. **Three-way merge**: How Git combines changes from different branches

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
\`\`\`

Finally, let's create a simple test script to verify the implementation:
