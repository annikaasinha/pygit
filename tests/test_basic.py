import os
import sys
import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add the parent directory to the path so we can import pygit
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygit.commands.init import init
from pygit.commands.add import add
from pygit.commands.commit import commit
from pygit.commands.status import status
from pygit.commands.log import log
from pygit.utils import read_index, get_head_commit

class TestBasicFunctionality(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test repository
        self.test_dir = tempfile.mkdtemp()
        self.old_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Initialize the repository
        init()
    
    def tearDown(self):
        # Clean up
        os.chdir(self.old_dir)
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test repository initialization."""
        # Check that the .pygit directory exists
        self.assertTrue(os.path.exists('.pygit'))
        self.assertTrue(os.path.exists('.pygit/objects'))
        self.assertTrue(os.path.exists('.pygit/refs/heads'))
        self.assertTrue(os.path.exists('.pygit/HEAD'))
    
    def test_add_commit(self):
        """Test adding files and committing."""
        # Create a test file
        with open('test.txt', 'w') as f:
            f.write('Hello, world!')
        
        # Add the file
        add(['test.txt'])
        
        # Check that the file is in the index
        index = read_index()
        self.assertIn('test.txt', index)
        
        # Commit the file
        commit('Initial commit', 'Test User <test@example.com>')
        
        # Check that we have a commit
        head_commit = get_head_commit()
        self.assertIsNotNone(head_commit)
    
    def test_multiple_commits(self):
        """Test making multiple commits."""
        # Create and commit a file
        with open('file1.txt', 'w') as f:
            f.write('File 1')
        
        add(['file1.txt'])
        commit('First commit', 'Test User <test@example.com>')
        
        # Create and commit another file
        with open('file2.txt', 'w') as f:
            f.write('File 2')
        
        add(['file2.txt'])
        commit('Second commit', 'Test User <test@example.com>')
        
        # Modify and commit the first file
        with open('file1.txt', 'w') as f:
            f.write('File 1 modified')
        
        add(['file1.txt'])
        commit('Third commit', 'Test User <test@example.com>')
        
        # Check that we have a commit history
        # This is a simple check - we'd need to capture output to verify log content
        head_commit = get_head_commit()
        self.assertIsNotNone(head_commit)

if __name__ == '__main__':
    unittest.main()
