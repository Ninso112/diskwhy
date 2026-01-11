# diskwhy

diskwhy is a lightweight command-line tool for Linux that helps you understand why your disk is full. It scans a directory tree, aggregates file sizes by directory and file type, and highlights large and old files in a concise, human-readable summary. Instead of parsing verbose `du` output, diskwhy provides a clear overview of which paths and file categories consume most of your storage space.

## Installation

### From Source

Clone the repository and install using pip:

```bash
git clone <repository-url>
cd diskwhy
pip install .
```

For development installation (editable mode):

```bash
pip install -e .
```

### Requirements

- Python 3.7 or higher
- Linux operating system
- Only Python standard library modules are used (no external dependencies)

## Usage

### Basic Usage

Scan the current directory:

```bash
diskwhy
```

This will show:
- Summary: total size, number of files and directories
- Top 10 directories by size
- Top 10 file types by size

### Scan a Specific Directory

```bash
diskwhy /home/user
```

### Customize Output

Show top 5 directories and top 5 file types:

```bash
diskwhy /home/user --top-dirs 5 --top-types 5
```

### Filter Large and Old Files

Find the 10 largest files in `/var` that are at least 100 MB and older than 90 days:

```bash
diskwhy /var --min-size 100M --older-than 90 --show-large-files 10
```

### JSON Output

Generate JSON output in addition to the human-readable format:

```bash
diskwhy / --json
```

The JSON output is printed after the human-readable output, separated by a marker. This is useful for scripting and integration with other tools.

### Follow Symbolic Links

By default, symbolic links are skipped. To follow them:

```bash
diskwhy /path/to/directory --follow-symlinks
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `PATH` | Path to scan (default: current directory `.`) |
| `--help` | Show help message and exit |
| `--version` | Show version number and exit |
| `--top-dirs N` | Show top N directories by size (default: 10) |
| `--top-types N` | Show top N file types by size (default: 10) |
| `--min-size SIZE` | Only consider files larger than SIZE (e.g., `100M`, `1G`, `50KiB`) |
| `--older-than DAYS` | Only consider files older than DAYS days |
| `--show-large-files N` | Show top N largest files |
| `--json` | Also output results as JSON |
| `--follow-symlinks` | Follow symbolic links (default: skip them) |

### Size Units

The `--min-size` option supports both SI (base 1000) and binary (base 1024) units:

- **SI units**: `K`, `M`, `G`, `T` (e.g., `100M` = 100,000,000 bytes)
- **Binary units**: `KiB`, `MiB`, `GiB`, `TiB` (e.g., `100MiB` = 104,857,600 bytes)
- **Legacy units**: `KB`, `MB`, `GB`, `TB` (treated as binary units)

Size units are case-insensitive. The output always uses binary units (KiB, MiB, GiB) for consistency with standard Linux tools like `du`.

## Examples

### Find Large Log Files

```bash
diskwhy /var/log --top-types 5 --show-large-files 20 --min-size 10M
```

### Analyze Home Directory

```bash
diskwhy ~ --top-dirs 10 --top-types 10
```

### Check Disk Usage with JSON Output

```bash
diskwhy / --json > disk_usage.json
```

### Find Old Large Files in Downloads

```bash
diskwhy ~/Downloads --older-than 180 --min-size 50M --show-large-files 15
```

## Output Format

### Human-Readable Output

The tool provides structured, tabular output with clear sections:

1. **Summary**: Total size scanned, number of files and directories, skipped paths (if any)
2. **Top directories by size**: Directory paths with sizes and percentages
3. **Top file types by size**: File extensions with sizes, file counts, and percentages
4. **Largest files**: Individual file paths with sizes (if `--show-large-files` is specified)

All sizes are displayed in human-readable binary units (KiB, MiB, GiB, TiB).

### JSON Output

When using `--json`, the output includes a JSON structure with the same information in machine-readable format:

```json
{
  "summary": {
    "total_size": 1073741824,
    "total_size_human": "1.00 GiB",
    "file_count": 1234,
    "dir_count": 56,
    "skipped_paths_count": 0
  },
  "top_directories": [...],
  "top_file_types": [...],
  "largest_files": [...],
  "skipped_paths": []
}
```

## Known Limitations

### Performance

- Scanning very large directory trees (e.g., the entire root filesystem with millions of files) can take significant time
- The tool processes files sequentially; performance depends on filesystem speed and system I/O capabilities
- For very large scans, consider using filters (e.g., `--min-size`) to reduce the number of files processed

### Permissions

- The tool may encounter permission errors when scanning system directories (e.g., `/root`, `/sys`, `/proc`)
- Paths that cannot be accessed are skipped and reported in the summary
- Running with appropriate permissions (e.g., `sudo`) may be necessary for system-wide scans

### Symbolic Links

- By default, symbolic links are not followed to avoid counting files multiple times or following circular references
- Use `--follow-symlinks` carefully, especially when scanning system directories, as it may lead to counting the same files multiple times

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file in the repository for the full license text.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.
