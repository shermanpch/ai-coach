import os
import platform
import shutil
from pathlib import Path
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from chatbot import config
from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)


def _fix_directory_permissions(directory_path: Path) -> None:
    """
    Fix permissions for ChromaDB directory and its contents.
    Cross-platform compatible - handles both Unix and Windows systems.

    Args:
        directory_path: Path to the directory to fix permissions for
    """
    try:
        # Check if we're on Windows
        is_windows = platform.system() == "Windows"

        if is_windows:
            # On Windows, skip chmod operations as the directory is accessible by default
            # Windows handles permissions differently through ACLs
            logger.info(
                f"Windows detected - skipping chmod operations for {directory_path}"
            )
            return

        # Unix/Linux/macOS permission handling
        directory_path.chmod(0o755)

        # Fix permissions for all files and subdirectories
        for item in directory_path.rglob("*"):
            if item.is_dir():
                item.chmod(0o755)
            else:
                item.chmod(0o644)

        logger.info(f"Fixed permissions for {directory_path}")
    except Exception as e:
        logger.warning(f"Could not fix permissions for {directory_path}: {e}")
        # Don't raise the exception - permission issues shouldn't break the app


def _set_path_permissions(path: Path, is_directory: bool = True) -> None:
    """
    Set permissions for a path in a cross-platform way.

    Args:
        path: Path to set permissions for
        is_directory: Whether the path is a directory
    """
    try:
        # Skip chmod on Windows
        if platform.system() == "Windows":
            return

        # Set Unix permissions
        if is_directory:
            path.chmod(0o755)
        else:
            path.chmod(0o644)
    except Exception as e:
        logger.warning(f"Could not set permissions for {path}: {e}")


def get_vectorstore(
    documents: Optional[List[Document]] = None, recreate: bool = False
) -> Chroma:
    """
    Initializes or loads a ChromaDB vector store.
    If documents are provided and recreate is False, it tries to add them if the DB is new.
    If recreate is True, it will delete existing and build anew with provided documents.
    If no documents and DB exists, it loads it.
    """
    # Initialize Sentence Transformers embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},  # Use 'cuda' if you have GPU available
        encode_kwargs={
            "normalize_embeddings": True
        },  # Normalize for better similarity search
    )

    # Ensure the persist directory exists with proper permissions
    persist_path = Path(config.CHROMA_PERSIST_DIR)
    if not persist_path.exists():
        try:
            persist_path.mkdir(parents=True, exist_ok=True)
            # Set proper permissions (cross-platform compatible)
            _set_path_permissions(persist_path, is_directory=True)
            logger.info(f"Created ChromaDB directory: {config.CHROMA_PERSIST_DIR}")
        except Exception as e:
            logger.error(f"Failed to create ChromaDB directory: {e}")
            raise

    # Check if DB needs to be recreated or if it exists
    db_exists = os.path.exists(config.CHROMA_PERSIST_DIR)

    # Fix permissions if directory exists but has permission issues
    if db_exists:
        try:
            # Try to fix permissions on the directory and its contents
            _fix_directory_permissions(persist_path)
        except Exception as e:
            logger.warning(
                f"Could not fix permissions for {config.CHROMA_PERSIST_DIR}: {e}"
            )

    if recreate and db_exists:
        # Delete existing database directory to recreate
        logger.info(
            f"Recreating DB: Removing existing directory {config.CHROMA_PERSIST_DIR}"
        )
        shutil.rmtree(config.CHROMA_PERSIST_DIR)
        db_exists = False

    if documents and (recreate or not db_exists):
        logger.info(
            f"Creating new ChromaDB vector store at {config.CHROMA_PERSIST_DIR} with {len(documents)} documents."
        )
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=config.CHROMA_PERSIST_DIR,
            collection_name=config.CHROMA_COLLECTION_NAME,
        )
        logger.info("Vector store created and persisted.")
    elif db_exists:
        logger.info(
            f"Loading existing ChromaDB vector store from {config.CHROMA_PERSIST_DIR}."
        )
        vectorstore = Chroma(
            persist_directory=config.CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=config.CHROMA_COLLECTION_NAME,
        )
        # If documents are provided and db exists, and not recreating, add them
        if documents and not recreate:
            logger.info(
                f"Adding {len(documents)} new documents to existing vector store."
            )
            vectorstore.add_documents(documents)
            logger.info("New documents added and persisted.")
    elif documents is None and not db_exists:
        raise ValueError(
            "No documents provided and no existing ChromaDB found to load."
        )
    else:  # documents provided, db exists, not recreating
        logger.info("Loading existing ChromaDB. Documents provided but not recreating.")
        vectorstore = Chroma(
            persist_directory=config.CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=config.CHROMA_COLLECTION_NAME,
        )

    return vectorstore


def add_documents_to_vectorstore(
    vectorstore: Chroma, documents: List[Document]
) -> None:
    """
    Add new documents to an existing vector store.

    Args:
        vectorstore: The existing Chroma vector store instance.
        documents: List of documents to add.
    """
    if not documents:
        logger.info("No documents provided to add.")
        return

    logger.info(f"Adding {len(documents)} documents to the vector store.")
    vectorstore.add_documents(documents)
    logger.info("Documents added and persisted successfully.")


def delete_vectorstore(persist_dir: Optional[str] = None) -> bool:
    """
    Delete the entire vector store directory.

    Args:
        persist_dir: Directory to delete. If None, uses config.CHROMA_PERSIST_DIR

    Returns:
        bool: True if successfully deleted, False otherwise
    """
    target_dir = persist_dir or config.CHROMA_PERSIST_DIR

    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
            logger.info(f"Successfully deleted vector store directory: {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vector store directory {target_dir}: {e}")
            return False
    else:
        logger.info(f"Vector store directory {target_dir} does not exist.")
        return True


def get_vectorstore_stats(vectorstore: Chroma) -> dict:
    """
    Get basic statistics about the vector store.

    Args:
        vectorstore: The Chroma vector store instance.

    Returns:
        dict: Statistics about the vector store
    """
    try:
        # Get the collection
        collection = vectorstore._collection

        # Get count of documents
        count = collection.count()

        stats = {
            "document_count": count,
            "collection_name": config.CHROMA_COLLECTION_NAME,
            "persist_directory": config.CHROMA_PERSIST_DIR,
            "embedding_model": config.EMBEDDING_MODEL_NAME,
        }

        return stats
    except Exception as e:
        return {"error": f"Failed to get stats: {e}"}


def get_vectorstore_path() -> Path:
    """Return the absolute path where the Chroma store is persisted."""
    return PROJECT_ROOT / config.CHROMA_PERSIST_DIR


def fix_vectorstore_permissions() -> bool:
    """
    Fix permissions for the vectorstore directory.

    Returns:
        bool: True if permissions were fixed successfully, False otherwise
    """
    try:
        vectorstore_path = get_vectorstore_path()
        if vectorstore_path.exists():
            _fix_directory_permissions(vectorstore_path)
            return True
        else:
            logger.info("Vectorstore directory does not exist, nothing to fix.")
            return True
    except Exception as e:
        logger.error(f"Failed to fix vectorstore permissions: {e}")
        return False
