"""
Core scanning and aggregation logic for diskwhy.
"""

import os
import stat
from pathlib import Path
from datetime import datetime, timedelta


def scan_directory(path, follow_symlinks=False):
    """
    Recursively scan a directory and collect file information.
    
    Args:
        path: Path to scan (str or Path object)
        follow_symlinks: Whether to follow symbolic links (default: False)
    
    Returns:
        tuple: (files_list, skipped_paths) where files_list contains dicts with
               file information and skipped_paths is a list of paths that couldn't
               be accessed
    """
    files_list = []
    skipped_paths = []
    path = Path(path).resolve()
    
    try:
        if not path.exists():
            skipped_paths.append(str(path))
            return files_list, skipped_paths
        
        if not path.is_dir():
            # If it's a file, process it directly
            try:
                file_stat = path.stat()
                file_info = {
                    "path": str(path),
                    "size": file_stat.st_size,
                    "mtime": file_stat.st_mtime,
                    "extension": _get_extension(path.name),
                }
                files_list.append(file_info)
            except (OSError, PermissionError) as e:
                skipped_paths.append(str(path))
            return files_list, skipped_paths
        
        # Use os.walk for efficient directory traversal
        for root, dirs, filenames in os.walk(path, followlinks=follow_symlinks):
            root_path = Path(root)
            
            # Process files in current directory
            for filename in filenames:
                file_path = root_path / filename
                
                # Skip symlinks if not following them
                if not follow_symlinks:
                    try:
                        if file_path.is_symlink():
                            continue
                    except OSError:
                        pass
                
                try:
                    file_stat = file_path.stat()
                    file_info = {
                        "path": str(file_path),
                        "size": file_stat.st_size,
                        "mtime": file_stat.st_mtime,
                        "extension": _get_extension(filename),
                    }
                    files_list.append(file_info)
                except (OSError, PermissionError):
                    skipped_paths.append(str(file_path))
    
    except (OSError, PermissionError) as e:
        skipped_paths.append(str(path))
    
    return files_list, skipped_paths


def _get_extension(filename):
    """
    Extract file extension from filename.
    
    Args:
        filename: Name of the file
    
    Returns:
        str: Extension (e.g., ".txt") or "no extension" if none
    """
    if not filename or filename == ".":
        return "no extension"
    
    # Handle hidden files (e.g., .bashrc)
    if filename.startswith(".") and "." not in filename[1:]:
        return "no extension"
    
    # Get the extension
    parts = filename.rsplit(".", 1)
    if len(parts) == 2 and parts[1]:
        return "." + parts[1].lower()
    
    return "no extension"


def aggregate_by_directory(files_list):
    """
    Aggregate file sizes by directory.
    
    Args:
        files_list: List of file info dictionaries
    
    Returns:
        dict: Mapping of directory paths to total sizes (in bytes)
    """
    dir_sizes = {}
    
    for file_info in files_list:
        file_path = Path(file_info["path"])
        directory = str(file_path.parent)
        size = file_info["size"]
        
        if directory not in dir_sizes:
            dir_sizes[directory] = 0
        dir_sizes[directory] += size
    
    return dir_sizes


def aggregate_by_filetype(files_list):
    """
    Aggregate file sizes by file extension/type.
    
    Args:
        files_list: List of file info dictionaries
    
    Returns:
        dict: Mapping of extensions to dicts with "total_size" and "file_count"
    """
    type_sizes = {}
    
    for file_info in files_list:
        ext = file_info["extension"]
        size = file_info["size"]
        
        if ext not in type_sizes:
            type_sizes[ext] = {"total_size": 0, "file_count": 0}
        
        type_sizes[ext]["total_size"] += size
        type_sizes[ext]["file_count"] += 1
    
    return type_sizes


def filter_files(files_list, min_size=None, older_than_days=None):
    """
    Filter files based on size and age criteria.
    
    Args:
        files_list: List of file info dictionaries
        min_size: Minimum file size in bytes (None to skip size filter)
        older_than_days: Files older than this many days (None to skip age filter)
    
    Returns:
        list: Filtered list of file info dictionaries
    """
    filtered = []
    cutoff_time = None
    
    if older_than_days is not None:
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        cutoff_timestamp = cutoff_time.timestamp()
    else:
        cutoff_timestamp = None
    
    for file_info in files_list:
        # Apply size filter
        if min_size is not None and file_info["size"] < min_size:
            continue
        
        # Apply age filter
        if cutoff_timestamp is not None:
            if file_info["mtime"] > cutoff_timestamp:
                continue
        
        filtered.append(file_info)
    
    return filtered


def get_largest_files(files_list, n, min_size=None, older_than_days=None):
    """
    Get the N largest files, optionally filtered by size and age.
    
    Args:
        files_list: List of file info dictionaries
        n: Number of files to return
        min_size: Minimum file size in bytes (None to skip size filter)
        older_than_days: Files older than this many days (None to skip age filter)
    
    Returns:
        list: Top N file info dictionaries, sorted by size (largest first)
    """
    # Apply filters
    filtered = filter_files(files_list, min_size=min_size, older_than_days=older_than_days)
    
    # Sort by size (descending)
    sorted_files = sorted(filtered, key=lambda x: x["size"], reverse=True)
    
    # Return top N
    return sorted_files[:n]
