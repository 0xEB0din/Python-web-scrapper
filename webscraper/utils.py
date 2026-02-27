import os
import re
import logging
from urllib.parse import urlparse, unquote


logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def setup_logging(verbose=False):
    """Configure root logger for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def validate_url(url):
    """Check that a URL has an HTTP(S) scheme and a valid host."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def sanitize_filename(name):
    """
    Remove path traversal sequences and filesystem-unsafe characters.

    This is the first line of defense against malicious filenames in downloaded
    content. Even if a server sends a crafted Content-Disposition header with
    directory traversal (../../etc/passwd), this will reduce it to a flat,
    safe filename.
    """
    name = unquote(name)
    # Strip directory components — we only want the basename
    name = os.path.basename(name)
    # Replace unsafe characters with underscores
    name = _UNSAFE_FILENAME_CHARS.sub("_", name)
    # Collapse runs of underscores and strip leading/trailing junk
    name = re.sub(r"_+", "_", name).strip("_. ")
    # Filesystem filename length limits (most cap at 255 bytes)
    name = name[:200]
    return name or "unnamed_file"


def safe_join(base_dir, filename):
    """
    Join a base directory and filename with path traversal protection.

    Defense-in-depth: even if sanitize_filename has a gap, this ensures the
    resolved path never escapes the intended output directory.
    """
    clean_name = sanitize_filename(filename)
    full_path = os.path.normpath(os.path.join(base_dir, clean_name))

    if not full_path.startswith(os.path.normpath(base_dir)):
        raise ValueError(f"Path traversal blocked: {filename}")

    return full_path


def make_output_dir(name, parent=None):
    """Create a download directory derived from a page title or custom name."""
    parent = parent or os.getcwd()
    dirname = sanitize_filename(name.replace(" ", "_"))
    path = os.path.join(parent, dirname)
    os.makedirs(path, exist_ok=True)
    return path
