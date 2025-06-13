import os
from typing import Any, Dict, Optional

from langchain.chains.query_constructor.base import (
    StructuredQueryOutputParser,
    get_query_constructor_prompt,
)
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_chroma import Chroma
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_openai import ChatOpenAI

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

from .attributes import PETERSON_METADATA_FIELDS

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def create_self_query_retriever(
    vectorstore: Chroma, llm_model: str = "openai/gpt-4o-mini", k: int = 12
) -> SelfQueryRetriever:
    """
    Create a SelfQueryRetriever for Peterson university data.

    This retriever can understand natural language queries and automatically
    construct appropriate metadata filters based on the comprehensive Peterson
    university dataset structure.

    Args:
        vectorstore: The Chroma vector store instance
        llm_model: The model to use for query construction (OpenRouter format)
        k: Number of documents to retrieve

    Returns:
        Configured SelfQueryRetriever instance
    """
    # Build query-constructor chain using OpenRouter
    llm = ChatOpenAI(
        model=llm_model,
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": "http://localhost:8000",  # Your app URL
            "X-Title": "AI College Coach",  # Your app name
        },
    )
    prompt = get_query_constructor_prompt(
        "Peterson's Guide university profiles with comprehensive data on admissions, costs, academics, athletics, and campus life",
        PETERSON_METADATA_FIELDS,
    )
    parser = StructuredQueryOutputParser.from_components()
    query_constructor = prompt | llm | parser  # LCEL pipeline

    # Create SelfQueryRetriever
    retriever = SelfQueryRetriever(
        query_constructor=query_constructor,
        vectorstore=vectorstore,
        structured_query_translator=ChromaTranslator(),
        search_kwargs={"k": k},
    )

    return retriever


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
