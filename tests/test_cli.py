"""
Unit tests for CLI argument parsing.
"""

import os
import sys
import unittest
import argparse
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from diskwhy import cli


class TestCLI(unittest.TestCase):
    """Test cases for CLI module."""
    
    def test_parse_size_kb(self):
        """Test parsing size strings (KB, KiB)."""
        self.assertEqual(cli.parse_size("1K"), 1000)
        self.assertEqual(cli.parse_size("1KB"), 1024)
        self.assertEqual(cli.parse_size("1KiB"), 1024)
        self.assertEqual(cli.parse_size("10K"), 10000)
        self.assertEqual(cli.parse_size("10KB"), 10240)
    
    def test_parse_size_mb(self):
        """Test parsing size strings (MB, MiB)."""
        self.assertEqual(cli.parse_size("1M"), 1000 ** 2)
        self.assertEqual(cli.parse_size("1MB"), 1024 ** 2)
        self.assertEqual(cli.parse_size("1MiB"), 1024 ** 2)
        self.assertEqual(cli.parse_size("100M"), 100 * 1000 ** 2)
    
    def test_parse_size_gb(self):
        """Test parsing size strings (GB, GiB)."""
        self.assertEqual(cli.parse_size("1G"), 1000 ** 3)
        self.assertEqual(cli.parse_size("1GB"), 1024 ** 3)
        self.assertEqual(cli.parse_size("1GiB"), 1024 ** 3)
    
    def test_parse_size_bytes(self):
        """Test parsing size strings without units."""
        self.assertEqual(cli.parse_size("1024"), 1024)
        self.assertEqual(cli.parse_size("0"), 0)
    
    def test_parse_size_decimal(self):
        """Test parsing decimal size strings."""
        self.assertEqual(cli.parse_size("1.5M"), int(1.5 * 1000 ** 2))
        self.assertEqual(cli.parse_size("2.5GiB"), int(2.5 * 1024 ** 3))
    
    def test_parse_size_case_insensitive(self):
        """Test that size parsing is case-insensitive."""
        self.assertEqual(cli.parse_size("1m"), 1000 ** 2)
        self.assertEqual(cli.parse_size("1M"), 1000 ** 2)
        self.assertEqual(cli.parse_size("1mib"), 1024 ** 2)
        self.assertEqual(cli.parse_size("1MiB"), 1024 ** 2)
    
    def test_parse_size_invalid(self):
        """Test parsing invalid size strings."""
        with self.assertRaises(ValueError):
            cli.parse_size("")
        
        with self.assertRaises(ValueError):
            cli.parse_size("abc")
        
        with self.assertRaises(ValueError):
            cli.parse_size("1X")
        
        with self.assertRaises(ValueError):
            cli.parse_size("invalid")
    
    @patch("sys.argv", ["diskwhy", "--help"])
    def test_parse_arguments_help(self):
        """Test argument parsing with --help."""
        # This should not raise, but argparse will print help and exit
        # We can't easily test this without mocking sys.exit
        pass
    
    def test_parse_arguments_defaults(self):
        """Test argument parsing with defaults."""
        with patch("sys.argv", ["diskwhy"]):
            args = cli.parse_arguments()
            self.assertEqual(args.path, ".")
            self.assertEqual(args.top_dirs, 10)
            self.assertEqual(args.top_types, 10)
            self.assertIsNone(args.min_size)
            self.assertIsNone(args.older_than)
            self.assertIsNone(args.show_large_files)
            self.assertFalse(args.json)
            self.assertFalse(args.follow_symlinks)
    
    def test_parse_arguments_path(self):
        """Test argument parsing with path."""
        with patch("sys.argv", ["diskwhy", "/home/user"]):
            args = cli.parse_arguments()
            self.assertEqual(args.path, "/home/user")
    
    def test_parse_arguments_options(self):
        """Test argument parsing with various options."""
        with patch("sys.argv", [
            "diskwhy",
            "/var",
            "--top-dirs", "5",
            "--top-types", "3",
            "--min-size", "100M",
            "--older-than", "90",
            "--show-large-files", "10",
            "--json",
            "--follow-symlinks"
        ]):
            args = cli.parse_arguments()
            self.assertEqual(args.path, "/var")
            self.assertEqual(args.top_dirs, 5)
            self.assertEqual(args.top_types, 3)
            self.assertEqual(args.min_size, "100M")
            self.assertEqual(args.older_than, 90)
            self.assertEqual(args.show_large_files, 10)
            self.assertTrue(args.json)
            self.assertTrue(args.follow_symlinks)


if __name__ == "__main__":
    unittest.main()
