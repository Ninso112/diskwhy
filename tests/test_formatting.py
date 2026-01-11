"""
Unit tests for formatting functions.
"""

import os
import sys
import json
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from diskwhy import formatting


class TestFormatting(unittest.TestCase):
    """Test cases for formatting module."""
    
    def test_format_size(self):
        """Test size formatting."""
        # Bytes
        self.assertEqual(formatting.format_size(0), "0 B")
        self.assertEqual(formatting.format_size(500), "500 B")
        self.assertEqual(formatting.format_size(1023), "1023 B")
        
        # KiB
        self.assertEqual(formatting.format_size(1024), "1.00 KiB")
        self.assertEqual(formatting.format_size(1536), "1.50 KiB")
        self.assertEqual(formatting.format_size(10240), "10.00 KiB")
        
        # MiB
        self.assertEqual(formatting.format_size(1024 ** 2), "1.00 MiB")
        self.assertEqual(formatting.format_size(2 * 1024 ** 2), "2.00 MiB")
        
        # GiB
        self.assertEqual(formatting.format_size(1024 ** 3), "1.00 GiB")
        
        # Large values
        self.assertIn("KiB", formatting.format_size(500 * 1024))
        self.assertIn("MiB", formatting.format_size(500 * 1024 ** 2))
        self.assertIn("GiB", formatting.format_size(500 * 1024 ** 3))
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        self.assertEqual(formatting.format_percentage(0, 100), "0.0%")
        self.assertEqual(formatting.format_percentage(25, 100), "25.0%")
        self.assertEqual(formatting.format_percentage(50, 100), "50.0%")
        self.assertEqual(formatting.format_percentage(100, 100), "100.0%")
        self.assertEqual(formatting.format_percentage(33, 100), "33.0%")
        self.assertEqual(formatting.format_percentage(33.33, 100), "33.3%")
        
        # Zero total
        self.assertEqual(formatting.format_percentage(50, 0), "0.0%")
    
    def test_format_summary(self):
        """Test summary formatting."""
        summary = formatting.format_summary(
            total_size=1024 * 1024,
            file_count=100,
            dir_count=10,
            skipped_paths=[]
        )
        
        self.assertIn("Summary", summary)
        self.assertIn("1.00 MiB", summary)
        self.assertIn("100", summary)
        self.assertIn("10", summary)
        
        # Test with skipped paths
        summary_with_skipped = formatting.format_summary(
            total_size=1024 * 1024,
            file_count=100,
            dir_count=10,
            skipped_paths=["/path1", "/path2"]
        )
        
        self.assertIn("Skipped paths", summary_with_skipped)
        self.assertIn("/path1", summary_with_skipped)
    
    def test_format_top_directories(self):
        """Test top directories formatting."""
        dirs_dict = {
            "/home/user/documents": 1024 * 1024 * 100,
            "/home/user/downloads": 1024 * 1024 * 50,
            "/home/user/videos": 1024 * 1024 * 200,
        }
        total_size = 1024 * 1024 * 350
        
        output = formatting.format_top_directories(dirs_dict, total_size, n=3)
        
        self.assertIn("Top directories by size", output)
        self.assertIn("/home/user/videos", output)
        self.assertIn("/home/user/documents", output)
        self.assertIn("/home/user/downloads", output)
        # Should be sorted by size
        videos_pos = output.find("/home/user/videos")
        documents_pos = output.find("/home/user/documents")
        downloads_pos = output.find("/home/user/downloads")
        self.assertLess(videos_pos, documents_pos)
        self.assertLess(documents_pos, downloads_pos)
    
    def test_format_top_filetypes(self):
        """Test top file types formatting."""
        types_dict = {
            ".txt": {"total_size": 1024 * 100, "file_count": 50},
            ".log": {"total_size": 1024 * 200, "file_count": 10},
            ".jpg": {"total_size": 1024 * 300, "file_count": 5},
        }
        total_size = 1024 * 600
        
        output = formatting.format_top_filetypes(types_dict, total_size, n=3)
        
        self.assertIn("Top file types by size", output)
        self.assertIn(".jpg", output)
        self.assertIn(".log", output)
        self.assertIn(".txt", output)
        # Should show file counts
        self.assertIn("5", output)
        self.assertIn("10", output)
        self.assertIn("50", output)
    
    def test_format_largest_files(self):
        """Test largest files formatting."""
        files_list = [
            {"path": "/path/to/file1.txt", "size": 1024 * 1024 * 100},
            {"path": "/path/to/file2.log", "size": 1024 * 1024 * 50},
            {"path": "/path/to/file3.jpg", "size": 1024 * 1024 * 200},
        ]
        
        output = formatting.format_largest_files(files_list, n=3)
        
        self.assertIn("Largest files", output)
        self.assertIn("file1.txt", output)
        self.assertIn("file2.log", output)
        self.assertIn("file3.jpg", output)
        # Should be sorted by size (file3.jpg is largest)
        file3_pos = output.find("file3.jpg")
        file1_pos = output.find("file1.txt")
        file2_pos = output.find("file2.log")
        self.assertLess(file3_pos, file1_pos)
        self.assertLess(file1_pos, file2_pos)
    
    def test_to_json(self):
        """Test JSON output conversion."""
        summary_data = {
            "total_size": 1024 * 1024 * 100,
            "file_count": 50,
            "dir_count": 5,
        }
        top_dirs = {
            "/home/user/documents": 1024 * 1024 * 60,
            "/home/user/downloads": 1024 * 1024 * 40,
        }
        top_types = {
            ".txt": {"total_size": 1024 * 50, "file_count": 30},
            ".log": {"total_size": 1024 * 50, "file_count": 20},
        }
        largest_files = [
            {"path": "/path/to/file1.txt", "size": 1024 * 1024 * 10, "mtime": 1234567890.0},
        ]
        skipped_paths = []
        
        json_str = formatting.to_json(
            summary_data,
            top_dirs,
            top_types,
            largest_files,
            skipped_paths
        )
        
        # Should be valid JSON
        data = json.loads(json_str)
        
        # Check structure
        self.assertIn("summary", data)
        self.assertIn("top_directories", data)
        self.assertIn("top_file_types", data)
        self.assertIn("largest_files", data)
        self.assertIn("skipped_paths", data)
        
        # Check summary
        self.assertEqual(data["summary"]["total_size"], 1024 * 1024 * 100)
        self.assertEqual(data["summary"]["file_count"], 50)
        self.assertEqual(data["summary"]["dir_count"], 5)
        
        # Check top directories
        self.assertEqual(len(data["top_directories"]), 2)
        
        # Check top file types
        self.assertEqual(len(data["top_file_types"]), 2)
        
        # Check largest files
        self.assertEqual(len(data["largest_files"]), 1)
        self.assertEqual(data["largest_files"][0]["path"], "/path/to/file1.txt")


if __name__ == "__main__":
    unittest.main()
