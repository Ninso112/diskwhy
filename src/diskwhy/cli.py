"""
Command-line interface for diskwhy.
"""

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from . import core
from . import formatting


def parse_size(size_str):
    """
    Parse size string to bytes.
    
    Supports both SI (K, M, G) and binary (KiB, MiB, GiB) units.
    
    Args:
        size_str: Size string (e.g., "100M", "1G", "50KiB")
    
    Returns:
        int: Size in bytes
    
    Raises:
        ValueError: If size string is invalid
    """
    size_str = size_str.strip().upper()
    
    if not size_str:
        raise ValueError("Empty size string")
    
    # Extract numeric part and unit
    unit_start = 0
    for i, char in enumerate(size_str):
        if not char.isdigit() and char != '.':
            unit_start = i
            break
    else:
        # No unit found, assume bytes
        return int(float(size_str))
    
    try:
        numeric_part = float(size_str[:unit_start])
    except ValueError:
        raise ValueError(f"Invalid numeric part in size string: {size_str}")
    
    unit = size_str[unit_start:]
    
    # Define multipliers
    multipliers = {
        # Binary units (base 1024)
        "KIB": 1024,
        "MIB": 1024 ** 2,
        "GIB": 1024 ** 3,
        "TIB": 1024 ** 4,
        # SI units (base 1000)
        "K": 1000,
        "M": 1000 ** 2,
        "G": 1000 ** 3,
        "T": 1000 ** 4,
        # Also support KB, MB, GB (treat as binary for compatibility)
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
    }
    
    if unit not in multipliers:
        raise ValueError(f"Unknown size unit: {unit}. Supported: K, M, G, KiB, MiB, GiB, KB, MB, GB")
    
    return int(numeric_part * multipliers[unit])


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Analyze disk usage by scanning directory trees, aggregating sizes "
                    "by directory and file type, and identifying large/old files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"diskwhy {__version__}",
    )
    
    parser.add_argument(
        "--top-dirs",
        type=int,
        default=10,
        metavar="N",
        help="Show top N directories by size (default: 10)",
    )
    
    parser.add_argument(
        "--top-types",
        type=int,
        default=10,
        metavar="N",
        help="Show top N file types by size (default: 10)",
    )
    
    parser.add_argument(
        "--min-size",
        type=str,
        metavar="SIZE",
        help="Only consider files larger than SIZE (e.g., 100M, 1G, 50KiB)",
    )
    
    parser.add_argument(
        "--older-than",
        type=int,
        metavar="DAYS",
        help="Only consider files older than DAYS days",
    )
    
    parser.add_argument(
        "--show-large-files",
        type=int,
        metavar="N",
        help="Show top N largest files",
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also output results as JSON",
    )
    
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links (default: skip them)",
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for diskwhy CLI.
    """
    args = parse_arguments()
    
    # Validate path
    scan_path = Path(args.path).expanduser().resolve()
    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse min_size
    min_size_bytes = None
    if args.min_size:
        try:
            min_size_bytes = parse_size(args.min_size)
        except ValueError as e:
            print(f"Error: Invalid size format: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Scan directory
    try:
        files_list, skipped_paths = core.scan_directory(scan_path, follow_symlinks=args.follow_symlinks)
    except Exception as e:
        print(f"Error: Failed to scan directory: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not files_list:
        print(f"No files found in: {scan_path}", file=sys.stderr)
        sys.exit(0)
    
    # Calculate summary
    total_size = sum(f["size"] for f in files_list)
    file_count = len(files_list)
    
    # Aggregate by directory
    dir_sizes = core.aggregate_by_directory(files_list)
    dir_count = len(dir_sizes)
    
    # Get top directories
    sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)
    top_dirs = dict(sorted_dirs[:args.top_dirs])
    
    # Aggregate by file type
    type_sizes = core.aggregate_by_filetype(files_list)
    
    # Get top file types
    sorted_types = sorted(
        type_sizes.items(),
        key=lambda x: x[1]["total_size"],
        reverse=True
    )
    top_types = dict(sorted_types[:args.top_types])
    
    # Get largest files (if requested)
    largest_files = []
    if args.show_large_files:
        largest_files = core.get_largest_files(
            files_list,
            args.show_large_files,
            min_size=min_size_bytes,
            older_than_days=args.older_than
        )
    
    # Prepare summary data
    summary_data = {
        "total_size": total_size,
        "file_count": file_count,
        "dir_count": dir_count,
    }
    
    # Format and output
    output = formatting.format_output(
        summary_data,
        top_dirs,
        top_types,
        largest_files,
        skipped_paths
    )
    
    print(output)
    
    # Output JSON if requested
    if args.json:
        json_output = formatting.to_json(
            summary_data,
            top_dirs,
            top_types,
            largest_files,
            skipped_paths
        )
        print("\n--- JSON Output ---\n")
        print(json_output)


if __name__ == "__main__":
    main()
