"""
Unit tests for core scanning and aggregation logic.
"""

import os
import sys
import tempfile
import shutil
import unittest
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from diskwhy import core


class TestCore(unittest.TestCase):
    """Test cases for core module."""
    
    def setUp(self):
        """Set up temporary test directory structure."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test directory structure
        # test_dir/
        #   file1.txt (100 bytes)
        #   file2.log (200 bytes)
        #   subdir/
        #     file3.txt (50 bytes)
        #     file4.jpg (300 bytes)
        #     empty.txt (0 bytes)
        
        # Create files
        (self.test_path / "file1.txt").write_bytes(b"x" * 100)
        (self.test_path / "file2.log").write_bytes(b"x" * 200)
        
        subdir = self.test_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_bytes(b"x" * 50)
        (subdir / "file4.jpg").write_bytes(b"x" * 300)
        (subdir / "empty.txt").write_bytes(b"")
        
        # Create a file without extension
        (self.test_path / "noext").write_bytes(b"x" * 75)
    
    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_scan_directory(self):
        """Test directory scanning."""
        files_list, skipped_paths = core.scan_directory(self.test_dir)
        
        # Should find 6 files
        self.assertEqual(len(files_list), 6)
        self.assertEqual(len(skipped_paths), 0)
        
        # Check that all files are present
        file_paths = {f["path"] for f in files_list}
        expected_paths = {
            str(self.test_path / "file1.txt"),
            str(self.test_path / "file2.log"),
            str(self.test_path / "subdir" / "file3.txt"),
            str(self.test_path / "subdir" / "file4.jpg"),
            str(self.test_path / "subdir" / "empty.txt"),
            str(self.test_path / "noext"),
        }
        self.assertEqual(file_paths, expected_paths)
        
        # Check file sizes
        files_dict = {f["path"]: f["size"] for f in files_list}
        self.assertEqual(files_dict[str(self.test_path / "file1.txt")], 100)
        self.assertEqual(files_dict[str(self.test_path / "file2.log")], 200)
        self.assertEqual(files_dict[str(self.test_path / "subdir" / "file3.txt")], 50)
        self.assertEqual(files_dict[str(self.test_path / "subdir" / "file4.jpg")], 300)
        self.assertEqual(files_dict[str(self.test_path / "subdir" / "empty.txt")], 0)
        self.assertEqual(files_dict[str(self.test_path / "noext")], 75)
    
    def test_scan_directory_single_file(self):
        """Test scanning a single file."""
        file_path = self.test_path / "file1.txt"
        files_list, skipped_paths = core.scan_directory(file_path)
        
        self.assertEqual(len(files_list), 1)
        self.assertEqual(files_list[0]["path"], str(file_path))
        self.assertEqual(files_list[0]["size"], 100)
    
    def test_scan_directory_nonexistent(self):
        """Test scanning a non-existent path."""
        nonexistent = self.test_path / "nonexistent"
        files_list, skipped_paths = core.scan_directory(nonexistent)
        
        self.assertEqual(len(files_list), 0)
        self.assertEqual(len(skipped_paths), 1)
        self.assertIn(str(nonexistent), skipped_paths)
    
    def test_get_extension(self):
        """Test extension extraction."""
        self.assertEqual(core._get_extension("file.txt"), ".txt")
        self.assertEqual(core._get_extension("file.log"), ".log")
        self.assertEqual(core._get_extension("file.tar.gz"), ".gz")
        self.assertEqual(core._get_extension("noext"), "no extension")
        self.assertEqual(core._get_extension(""), "no extension")
        self.assertEqual(core._get_extension(".hidden"), "no extension")
        self.assertEqual(core._get_extension("file.TXT"), ".txt")  # lowercase
    
    def test_aggregate_by_directory(self):
        """Test directory aggregation."""
        files_list, _ = core.scan_directory(self.test_dir)
        dir_sizes = core.aggregate_by_directory(files_list)
        
        # Should have 2 directories: test_dir and test_dir/subdir
        self.assertGreaterEqual(len(dir_sizes), 2)
        
        # Check sizes
        test_dir_str = str(self.test_path)
        subdir_str = str(self.test_path / "subdir")
        
        # test_dir contains: file1.txt (100), file2.log (200), noext (75) = 375
        # subdir contains: file3.txt (50), file4.jpg (300), empty.txt (0) = 350
        self.assertEqual(dir_sizes[test_dir_str], 375)
        self.assertEqual(dir_sizes[subdir_str], 350)
    
    def test_aggregate_by_filetype(self):
        """Test file type aggregation."""
        files_list, _ = core.scan_directory(self.test_dir)
        type_sizes = core.aggregate_by_filetype(files_list)
        
        # Should have: .txt, .log, .jpg, no extension
        self.assertIn(".txt", type_sizes)
        self.assertIn(".log", type_sizes)
        self.assertIn(".jpg", type_sizes)
        self.assertIn("no extension", type_sizes)
        
        # Check sizes: .txt files: 100 + 50 + 0 = 150
        self.assertEqual(type_sizes[".txt"]["total_size"], 150)
        self.assertEqual(type_sizes[".txt"]["file_count"], 3)
        
        # .log files: 200
        self.assertEqual(type_sizes[".log"]["total_size"], 200)
        self.assertEqual(type_sizes[".log"]["file_count"], 1)
        
        # .jpg files: 300
        self.assertEqual(type_sizes[".jpg"]["total_size"], 300)
        self.assertEqual(type_sizes[".jpg"]["file_count"], 1)
        
        # no extension: 75
        self.assertEqual(type_sizes["no extension"]["total_size"], 75)
        self.assertEqual(type_sizes["no extension"]["file_count"], 1)
    
    def test_filter_files_by_size(self):
        """Test file filtering by size."""
        files_list, _ = core.scan_directory(self.test_dir)
        
        # Filter files >= 100 bytes
        filtered = core.filter_files(files_list, min_size=100)
        
        # Should have: file1.txt (100), file2.log (200), file4.jpg (300), noext (75 is filtered out)
        self.assertEqual(len(filtered), 3)
        sizes = {f["size"] for f in filtered}
        self.assertEqual(sizes, {100, 200, 300})
    
    def test_filter_files_by_age(self):
        """Test file filtering by age."""
        files_list, _ = core.scan_directory(self.test_dir)
        
        # Filter files older than 0 days (all files)
        filtered = core.filter_files(files_list, older_than_days=0)
        self.assertEqual(len(filtered), 0)  # No files older than "now"
        
        # Filter files older than 365 days (should be all files)
        filtered = core.filter_files(files_list, older_than_days=365)
        self.assertEqual(len(filtered), len(files_list))
    
    def test_filter_files_by_size_and_age(self):
        """Test file filtering by both size and age."""
        files_list, _ = core.scan_directory(self.test_dir)
        
        # Filter: size >= 100 AND older than 365 days
        filtered = core.filter_files(
            files_list,
            min_size=100,
            older_than_days=365
        )
        
        # Should have files >= 100 bytes: file1.txt, file2.log, file4.jpg
        self.assertEqual(len(filtered), 3)
    
    def test_get_largest_files(self):
        """Test getting largest files."""
        files_list, _ = core.scan_directory(self.test_dir)
        
        # Get top 3 largest files
        largest = core.get_largest_files(files_list, n=3)
        
        self.assertEqual(len(largest), 3)
        # Should be sorted by size (descending)
        sizes = [f["size"] for f in largest]
        self.assertEqual(sizes, [300, 200, 100])
    
    def test_get_largest_files_with_filters(self):
        """Test getting largest files with filters."""
        files_list, _ = core.scan_directory(self.test_dir)
        
        # Get top 2 largest files with min_size >= 150
        largest = core.get_largest_files(files_list, n=2, min_size=150)
        
        self.assertEqual(len(largest), 2)
        sizes = [f["size"] for f in largest]
        self.assertEqual(sizes, [300, 200])


if __name__ == "__main__":
    unittest.main()
