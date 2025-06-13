import os
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

    # Check if DB needs to be recreated or if it exists
    db_exists = os.path.exists(config.CHROMA_PERSIST_DIR)

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
