
import zipfile
from pathlib import Path

# Original ZIP file in Downloads
downloads = Path.home() / "Downloads"
source = downloads / "SWM_project.zip"

# Output ZIP file
output = downloads / "SWM_project_source_only.zip"

# Folders to exclude
excluded_dirs = {
    "venv",
    "venv312",
    ".venv",
    "node_modules",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "site-packages",
    "dist",
    "build",
}

# Files to exclude
excluded_files = {
    ".env",
    "ecoloop.db",
    "ecoloop.sqlite",
    "db.sqlite3",
}

excluded_suffixes = {".pyc", ".pyo", ".log"}

# Check that the original ZIP exists
if not source.is_file():
    print("ERROR: Original ZIP file was not found.")
    print(f"Expected location: {source}")
    print("Check the filename in your Downloads folder.")
    raise SystemExit(1)

# Avoid overwriting the original ZIP
if source.resolve() == output.resolve():
    print("ERROR: Input and output paths must be different.")
    raise SystemExit(1)

# Remove an old output ZIP if it exists
try:
    if output.exists():
        output.unlink()
except PermissionError:
    print("ERROR: Cannot replace the output ZIP.")
    print("Close the ZIP in File Explorer and run again.")
    raise SystemExit(1)

kept = 0
skipped = 0
kept_bytes = 0

print(f"Reading: {source}")
print("Creating cleaned ZIP. Please wait...")

try:
    with zipfile.ZipFile(source, "r") as zin:
        with zipfile.ZipFile(
            output,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=3,
            allowZip64=True,
        ) as zout:

            for item in zin.infolist():
                path = item.filename.replace("\\", "/")
                parts = path.split("/")
                name = parts[-1] if parts else ""

                # Skip common virtual environments and generated folders
                if any(
                    part.lower() in excluded_dirs
                    for part in parts
                ):
                    skipped += 1
                    continue

                # Skip secrets, local databases, and generated files
                if name.lower() in excluded_files:
                    skipped += 1
                    continue

                if name.lower().startswith(".env."):
                    skipped += 1
                    continue

                if Path(name).suffix.lower() in excluded_suffixes:
                    skipped += 1
                    continue

                # Preserve the folder structure and file contents
                if item.is_dir():
                    zout.writestr(item, b"")
                else:
                    with zin.open(item, "r") as file_in:
                        zout.writestr(item, file_in.read())
                    kept_bytes += item.file_size

                kept += 1

except PermissionError:
    print("\nERROR: Permission denied.")
    print("Close the ZIP file if it is open and try again.")
    raise SystemExit(1)

except zipfile.BadZipFile:
    print("\nERROR: The original ZIP file is invalid or incomplete.")
    raise SystemExit(1)

except OSError as error:
    print(f"\nERROR: {error}")
    raise SystemExit(1)

print("\nSUCCESS: Cleaned ZIP created.")
print(f"Output file: {output}")
print(f"Entries retained: {kept}")
print(f"Entries skipped: {skipped}")
print(f"Uncompressed retained data: {kept_bytes / (1024 * 1024):.1f} MB")
print(f"Output ZIP size: {output.stat().st_size / (1024 * 1024):.1f} MB")
print("\nUpload SWM_project_source_only.zip to this chat.")
