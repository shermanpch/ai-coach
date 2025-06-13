import os
from typing import Any, Dict, Optional

from langchain_chroma import Chroma

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def query_vectorstore(
    vectorstore: Chroma,
    query_text: str,
    k: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None,
    with_scores: bool = False,
):
    """
    Retrieve documents from the vector store, optionally with similarity scores.

    There are two retrieval modes:
    - If with_scores=False (default): returns a list of Documents, using LangChain's retriever interface. This is higher-level and does not provide similarity scores.
    - If with_scores=True: returns a list of (Document, score) tuples, using Chroma's similarity_search_with_score. This provides both the document and its similarity score to the query.

    Args:
        vectorstore: The Chroma vector store instance.
        query_text: The text to search for.
        k: The number of documents to return.
        metadata_filter: A dictionary for filtering metadata.
        with_scores: If True, return (Document, score) tuples. If False, return Documents only.

    Returns:
        List[Document] or List[tuple[Document, float]]
    """
    if with_scores:
        if metadata_filter:
            return vectorstore.similarity_search_with_score(
                query=query_text, k=k, filter=metadata_filter
            )
        else:
            return vectorstore.similarity_search_with_score(query=query_text, k=k)
    else:
        if metadata_filter:
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k, "filter": metadata_filter},
            )
        else:
            retriever = vectorstore.as_retriever(
                search_type="similarity", search_kwargs={"k": k}
            )
        return retriever.invoke(query_text)
