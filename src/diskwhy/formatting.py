"""
Output formatting functions for diskwhy.
"""

import json
from datetime import datetime


def format_size(size_bytes):
    """
    Convert bytes to human-readable format using binary units (KiB, MiB, GiB).
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        str: Formatted size string (e.g., "1.5 MiB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    
    units = ["KiB", "MiB", "GiB", "TiB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    # Format with appropriate precision
    if size >= 100:
        return f"{size:.1f} {units[unit_index]}"
    elif size >= 10:
        return f"{size:.2f} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_percentage(part, total):
    """
    Calculate and format percentage.
    
    Args:
        part: Part value
        total: Total value
    
    Returns:
        str: Percentage string (e.g., "25.5%")
    """
    if total == 0:
        return "0.0%"
    percentage = (part / total) * 100
    return f"{percentage:.1f}%"


def format_summary(total_size, file_count, dir_count, skipped_paths):
    """
    Format summary section.
    
    Args:
        total_size: Total size in bytes
        file_count: Number of files
        dir_count: Number of directories (approximate, based on directory aggregation)
        skipped_paths: List of skipped paths
    
    Returns:
        str: Formatted summary text
    """
    lines = []
    lines.append("Summary")
    lines.append("=" * 70)
    lines.append(f"Total size scanned: {format_size(total_size)}")
    lines.append(f"Number of files: {file_count:,}")
    lines.append(f"Number of directories: {dir_count:,}")
    
    if skipped_paths:
        lines.append(f"Skipped paths (permission denied): {len(skipped_paths)}")
        # Show first few skipped paths
        for path in skipped_paths[:5]:
            lines.append(f"  - {path}")
        if len(skipped_paths) > 5:
            lines.append(f"  ... and {len(skipped_paths) - 5} more")
    
    lines.append("")
    return "\n".join(lines)


def format_top_directories(dirs_dict, total_size, n):
    """
    Format top directories table.
    
    Args:
        dirs_dict: Dictionary mapping directory paths to sizes
        total_size: Total size for percentage calculation
        n: Number of directories to show
    
    Returns:
        str: Formatted table text
    """
    if not dirs_dict:
        return ""
    
    # Sort by size and get top N
    sorted_dirs = sorted(dirs_dict.items(), key=lambda x: x[1], reverse=True)[:n]
    
    lines = []
    lines.append("Top directories by size")
    lines.append("=" * 70)
    lines.append(f"{'Directory':<50} {'Size':>12} {'Percentage':>10}")
    lines.append("-" * 70)
    
    for directory, size in sorted_dirs:
        # Truncate long directory names
        display_dir = directory if len(directory) <= 48 else "..." + directory[-45:]
        size_str = format_size(size)
        percentage = format_percentage(size, total_size)
        lines.append(f"{display_dir:<50} {size_str:>12} {percentage:>10}")
    
    lines.append("")
    return "\n".join(lines)


def format_top_filetypes(types_dict, total_size, n):
    """
    Format top file types table.
    
    Args:
        types_dict: Dictionary mapping extensions to dicts with "total_size" and "file_count"
        total_size: Total size for percentage calculation
        n: Number of file types to show
    
    Returns:
        str: Formatted table text
    """
    if not types_dict:
        return ""
    
    # Sort by size and get top N
    sorted_types = sorted(
        types_dict.items(),
        key=lambda x: x[1]["total_size"],
        reverse=True
    )[:n]
    
    lines = []
    lines.append("Top file types by size")
    lines.append("=" * 70)
    lines.append(f"{'Extension':<20} {'Size':>12} {'Files':>10} {'Percentage':>10}")
    lines.append("-" * 70)
    
    for ext, data in sorted_types:
        size_str = format_size(data["total_size"])
        file_count = data["file_count"]
        percentage = format_percentage(data["total_size"], total_size)
        lines.append(f"{ext:<20} {size_str:>12} {file_count:>10,} {percentage:>10}")
    
    lines.append("")
    return "\n".join(lines)


def format_largest_files(files_list, n):
    """
    Format largest files list.
    
    Args:
        files_list: List of file info dictionaries (already sorted)
        n: Number of files to show
    
    Returns:
        str: Formatted list text
    """
    if not files_list:
        return ""
    
    # Take top N
    top_files = files_list[:n]
    
    lines = []
    lines.append("Largest files")
    lines.append("=" * 70)
    lines.append(f"{'File':<50} {'Size':>12}")
    lines.append("-" * 70)
    
    for file_info in top_files:
        file_path = file_info["path"]
        # Truncate long file paths
        display_path = file_path if len(file_path) <= 48 else "..." + file_path[-45:]
        size_str = format_size(file_info["size"])
        lines.append(f"{display_path:<50} {size_str:>12}")
    
    lines.append("")
    return "\n".join(lines)


def format_output(summary_data, top_dirs, top_types, largest_files, skipped_paths):
    """
    Orchestrate all formatting functions to create complete output.
    
    Args:
        summary_data: Dict with "total_size", "file_count", "dir_count"
        top_dirs: Dictionary of top directories with sizes
        top_types: Dictionary of top file types with sizes and counts
        largest_files: List of largest file info dictionaries
        skipped_paths: List of skipped paths
    
    Returns:
        str: Complete formatted output
    """
    lines = []
    
    # Summary
    lines.append(format_summary(
        summary_data["total_size"],
        summary_data["file_count"],
        summary_data["dir_count"],
        skipped_paths
    ))
    
    # Top directories
    if top_dirs:
        lines.append(format_top_directories(
            top_dirs,
            summary_data["total_size"],
            len(top_dirs)
        ))
    
    # Top file types
    if top_types:
        lines.append(format_top_filetypes(
            top_types,
            summary_data["total_size"],
            len(top_types)
        ))
    
    # Largest files
    if largest_files:
        lines.append(format_largest_files(
            largest_files,
            len(largest_files)
        ))
    
    return "\n".join(lines)


def to_json(summary_data, top_dirs, top_types, largest_files, skipped_paths):
    """
    Convert aggregated data to JSON format.
    
    Args:
        summary_data: Dict with "total_size", "file_count", "dir_count"
        top_dirs: Dictionary of top directories with sizes
        top_types: Dictionary of top file types with sizes and counts
        largest_files: List of largest file info dictionaries
        skipped_paths: List of skipped paths
    
    Returns:
        str: JSON string representation
    """
    # Convert top_dirs to list of dicts
    dirs_list = [
        {"directory": dir_path, "size": size}
        for dir_path, size in sorted(top_dirs.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Convert top_types to list of dicts
    types_list = [
        {
            "extension": ext,
            "total_size": data["total_size"],
            "file_count": data["file_count"]
        }
        for ext, data in sorted(
            top_types.items(),
            key=lambda x: x[1]["total_size"],
            reverse=True
        )
    ]
    
    # Convert largest_files to list (already sorted)
    files_list = [
        {
            "path": f["path"],
            "size": f["size"],
            "mtime": f["mtime"]
        }
        for f in largest_files
    ]
    
    output = {
        "summary": {
            "total_size": summary_data["total_size"],
            "total_size_human": format_size(summary_data["total_size"]),
            "file_count": summary_data["file_count"],
            "dir_count": summary_data["dir_count"],
            "skipped_paths_count": len(skipped_paths)
        },
        "top_directories": dirs_list,
        "top_file_types": types_list,
        "largest_files": files_list,
        "skipped_paths": skipped_paths
    }
    
    return json.dumps(output, indent=2)
