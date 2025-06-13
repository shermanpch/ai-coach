import os
import sys
from functools import lru_cache
from pathlib import Path

# Module-level cache for paths and setup state
_PROJECT_ROOT_CACHE: Path | None = None
_LOGS_DIR_CACHE: Path | None = None
_SETUP_COMPLETED = False
_ERROR_MESSAGE_CACHE: str | None = None


@lru_cache(maxsize=1)
def find_project_root() -> Path:
    """
    Finds the project root directory.
    Assumes the project root contains a '.git' directory or 'pyproject.toml'.
    Traverses up from the location of this file.
    Caches the result.
    """
    global _PROJECT_ROOT_CACHE, _ERROR_MESSAGE_CACHE
    if _PROJECT_ROOT_CACHE:
        return _PROJECT_ROOT_CACHE

    try:
        current_path = Path(__file__).resolve()
        # Traverse up to find .git or pyproject.toml
        while current_path != current_path.parent:
            if (current_path / ".git").exists() or (
                current_path / "pyproject.toml"
            ).exists():
                _PROJECT_ROOT_CACHE = current_path
                return current_path
            current_path = current_path.parent
        # If loop finishes, root wasn't found by marker
        raise RuntimeError("Project root (.git or pyproject.toml marker) not found.")
    except Exception as e:
        _ERROR_MESSAGE_CACHE = f"Error finding project root: {e}"
        raise RuntimeError(_ERROR_MESSAGE_CACHE) from e


def get_project_root() -> Path:
    """Returns the cached project root, finding it if necessary."""
    if _ERROR_MESSAGE_CACHE:  # If find_project_root failed earlier
        raise RuntimeError(
            f"Cannot get project root due to previous error: {_ERROR_MESSAGE_CACHE}"
        )
    if _PROJECT_ROOT_CACHE is None:
        return find_project_root()  # This will cache it or raise error
    return _PROJECT_ROOT_CACHE


def get_logs_dir() -> Path:
    """Returns the path to the logs directory, creating it if it doesn't exist."""
    global _LOGS_DIR_CACHE
    if _LOGS_DIR_CACHE:
        return _LOGS_DIR_CACHE

    project_root = get_project_root()
    logs_dir = project_root / "logs"
    _LOGS_DIR_CACHE = logs_dir
    return logs_dir


def setup_project_environment() -> tuple[Path, Path]:
    """
    Sets up the project environment:
    1. Determines the project root.
    2. Changes the current working directory to the project root.
    3. Ensures the 'logs' directory exists.
    This function is idempotent and should be called once at the start of scripts/tests.
    sys.path manipulation for project modules is handled by 'pip install -e .'
    """
    global _SETUP_COMPLETED, _ERROR_MESSAGE_CACHE

    if _ERROR_MESSAGE_CACHE:  # Check if find_project_root already failed
        print(
            f"CRITICAL: Project environment setup cannot proceed due to error: {_ERROR_MESSAGE_CACHE}",
            file=sys.stderr,
        )
        sys.exit(1)

    if _SETUP_COMPLETED:
        # Ensure paths are valid even if setup was already done
        if not _PROJECT_ROOT_CACHE or not _LOGS_DIR_CACHE:
            # This should not happen if _SETUP_COMPLETED is True and no error occurred
            print(
                "CRITICAL: Inconsistent state in setup_project_environment.",
                file=sys.stderr,
            )
            sys.exit(1)
        return _PROJECT_ROOT_CACHE, _LOGS_DIR_CACHE

    try:
        project_r = get_project_root()  # Finds and caches root
        logs_d = get_logs_dir()  # Gets cached logs_dir path

        # Change current working directory to project root
        os.chdir(project_r)

        # Create logs directory
        logs_d.mkdir(exist_ok=True)

        _SETUP_COMPLETED = True
        return project_r, logs_d
    except Exception as e:
        _ERROR_MESSAGE_CACHE = f"Failed during project environment setup: {e}"
        print(f"CRITICAL: {_ERROR_MESSAGE_CACHE}", file=sys.stderr)
        sys.exit(1)
