import traceback

import chainlit as cl
from dotenv import load_dotenv

from chatbot.components import data_loader
from chatbot.components import retriever as retriever_component
from chatbot.components import vectorstore as vectorstore_component
from projectutils.logger import setup_logger

load_dotenv()

# Setup logger
logger = setup_logger(__file__)

# Global variable to hold the initialized vectorstore
db_vectorstore = None
_vectorstore_initialized = False


async def initialize_vectorstore():
    """Initialize the vectorstore once globally."""
    global db_vectorstore, _vectorstore_initialized

    if _vectorstore_initialized:
        return

    try:
        # Check if vectorstore already exists
        vectorstore_exists = vectorstore_component.get_vectorstore_path().exists()

        if vectorstore_exists:
            logger.info("Loading existing vectorstore...")
            # Load existing vectorstore without documents
            db_vectorstore = vectorstore_component.get_vectorstore(recreate=False)

            # Get stats about the existing vectorstore
            stats = vectorstore_component.get_vectorstore_stats(db_vectorstore)
            doc_count = stats.get("document_count", "unknown")
            logger.info(f"Vectorstore loaded with {doc_count} documents")
        else:
            logger.info("Creating new vectorstore...")
            # Load documents only when creating new vectorstore
            docs = data_loader.load_university_documents()
            logger.info(f"Processing {len(docs)} university documents...")

            # Create new vectorstore with documents
            db_vectorstore = vectorstore_component.get_vectorstore(
                documents=docs, recreate=False
            )
            logger.info(f"New vectorstore created with {len(docs)} documents")

        _vectorstore_initialized = True

    except Exception as e:
        logger.error(f"Error initializing vectorstore: {e}")
        raise e


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session - vectorstore is already loaded globally."""
    global db_vectorstore, _vectorstore_initialized

    logger.info("Starting new chat session")

    # Send initial welcome message
    await cl.Message(
        content="🎓 **Welcome to the AI College Coach!**\n\nInitializing the system..."
    ).send()

    try:
        # Initialize vectorstore if not already done
        if not _vectorstore_initialized:
            logger.info("First-time vectorstore initialization")
            # Send loading message
            loading_msg = cl.Message(
                content="📚 Loading vectorstore for the first time..."
            )
            await loading_msg.send()

            await initialize_vectorstore()

            # Send completion message for first-time initialization
            await cl.Message(
                content="✅ **System Ready!**\n\nVectorstore loaded successfully.\n\nYou can now ask questions about universities, admissions, tuition, programs, and more!"
            ).send()
        else:
            logger.info("Vectorstore already initialized, skipping reload")
            # Send ready message for subsequent chats
            await cl.Message(
                content="✅ **System Ready!**\n\nVectorstore is loaded with university documents.\n\nYou can now ask questions about universities, admissions, tuition, programs, and more!"
            ).send()

        logger.info("Chat session initialized successfully")

    except Exception as e:
        logger.error(f"Error during chat initialization: {e}")
        # Get the full traceback for debugging
        error_traceback = traceback.format_exc()
        logger.error(f"Full traceback: {error_traceback}")

        # Send detailed error message
        error_message = f"""
        ❌ **Error initializing system:**

            **Error Type:** {type(e).__name__}
            **Error Message:** {str(e)}

            **Full Traceback:**
            ```
            {error_traceback}
        ```

        Please check the logs or contact support if the issue persists.
        """

        await cl.Message(content=error_message).send()


@cl.on_chat_resume
async def on_chat_resume(thread):
    """Handle chat resume - ensure vectorstore is available."""
    global db_vectorstore, _vectorstore_initialized

    logger.info(f"Resuming chat session for thread: {thread}")

    if not _vectorstore_initialized:
        logger.warning("Vectorstore not initialized during resume, initializing now")
        await initialize_vectorstore()


@cl.on_message
async def main(message: cl.Message):
    """Handle user queries and return retrieved documents with similarity scores."""
    global db_vectorstore, _vectorstore_initialized

    logger.info(
        f"Received user query: {message.content[:100]}..."
    )  # Log first 100 chars

    # Ensure vectorstore is initialized
    if not _vectorstore_initialized or db_vectorstore is None:
        logger.warning("Vectorstore not initialized, initializing now")
        await cl.Message(
            content="⚠️ Vectorstore not initialized. Initializing now..."
        ).send()
        try:
            await initialize_vectorstore()
            await cl.Message(
                content="✅ Vectorstore initialized successfully! Please try your query again."
            ).send()
            return
        except Exception as e:
            logger.error(f"Failed to initialize vectorstore: {e}")
            await cl.Message(
                content=f"❌ Failed to initialize vectorstore: {str(e)}"
            ).send()
            return

    # Get the user's query
    query = message.content

    try:
        logger.info("Creating self query retriever")
        # Test SelfQueryRetriever with metadata filtering
        self_query_retriever = retriever_component.create_self_query_retriever(
            vectorstore=db_vectorstore, k=3
        )

        # Get the structured query to show the metadata filter
        structured_query = self_query_retriever.query_constructor.invoke(
            {"query": query}
        )
        logger.info(f"Structured query: {structured_query}")

        retrieved_docs = self_query_retriever.invoke(query)

        logger.info(f"Retrieved {len(retrieved_docs)} documents for query")

        # Check if any results were found
        if not retrieved_docs:
            logger.info("No documents found for query")

            # Show the structured query info even when no results found
            no_results_content = "No documents found for your query.\n\n"

            # Add structured query information
            if hasattr(structured_query, "query") and structured_query.query:
                no_results_content += f"**Search Query:** `{structured_query.query}`\n"

            if hasattr(structured_query, "filter") and structured_query.filter:
                no_results_content += (
                    f"**Metadata Filter:** `{structured_query.filter}`\n"
                )
            else:
                no_results_content += (
                    "**Metadata Filter:** No specific filters applied\n"
                )

            await cl.Message(content=no_results_content).send()
            return

        # Send a summary message with the structured query info
        summary_content = (
            f"Found {len(retrieved_docs)} relevant documents for your query:\n\n"
        )

        # Add structured query information
        if hasattr(structured_query, "query") and structured_query.query:
            summary_content += f"**Search Query:** `{structured_query.query}`\n"

        if hasattr(structured_query, "filter") and structured_query.filter:
            summary_content += f"**Metadata Filter:** `{structured_query.filter}`\n"
        else:
            summary_content += "**Metadata Filter:** No specific filters applied\n"

        await cl.Message(content=summary_content).send()

        # Collect elements for the side panel
        side_panel_elements = []

        # Iterate through results and display each one
        for i, doc in enumerate(retrieved_docs, 1):
            # Format the document content for display
            source = doc.metadata.get("source", "N/A")
            document_id = doc.metadata.get("document_id", "N/A")
            university_name = doc.metadata.get("university_name", "N/A")
            url = doc.metadata.get("url", "N/A")

            logger.debug(f"Processing result {i}: {university_name}")

            # Start with the result header
            output_content = f"# Result {i}\n\n"

            # Add the full markdown content (rendered)
            output_content += doc.page_content + "\n\n"

            # Add a separator before metadata
            output_content += "---\n\n"

            # Format metadata section nicely
            output_content += "## Document Metadata\n\n"

            # Core metadata in a structured format
            output_content += "| Field | Value |\n"
            output_content += "|-------|-------|\n"
            output_content += f"| **URL** | {url} |\n"
            output_content += f"| **University** | {university_name} |\n"
            output_content += f"| **Document ID** | {document_id} |\n"
            output_content += f"| **Source** | {source} |\n"

            # Add additional metadata if available
            if doc.metadata:
                filtered_metadata = {
                    k: v
                    for k, v in doc.metadata.items()
                    if k not in ["source", "document_id", "university_name", "url"]
                }
                if filtered_metadata:
                    output_content += "\n### Additional Metadata\n\n"
                    for key, value in filtered_metadata.items():
                        # Format the key nicely (replace underscores with spaces and title case)
                        formatted_key = key.replace("_", " ").title()
                        output_content += f"- **{formatted_key}:** {value}\n"

            # Create a text element for the side panel with the full document content
            text_element = cl.Text(
                name=f"Document {i}: {university_name}",
                content=output_content,
                display="side",
            )
            side_panel_elements.append(text_element)

            # Send a summary message with reference to the side panel document
            summary_content = f"## Result {i}: {university_name}\n\n"
            summary_content += f"**Peterson URL:** `{url}`\n"
            summary_content += f"**Source:** `{source}`\n"
            summary_content += f"**Document ID:** `{document_id}`\n\n"
            summary_content += f"📄 Click on **Document {i}: {university_name}** in the side panel to view the full document content.\n\n"

            await cl.Message(
                content=summary_content,
                elements=[text_element],
                author="Retriever",
            ).send()

        logger.info(f"Successfully processed and sent {len(retrieved_docs)} results")

    except Exception as e:
        logger.error(f"Error during document retrieval: {e}")
        # Get the full traceback for debugging
        error_traceback = traceback.format_exc()
        logger.error(f"Full traceback: {error_traceback}")

        # Send detailed error message
        error_message = f"""
        ❌ **Error during document retrieval:**

        **Error Type:** {type(e).__name__}
        **Error Message:** {str(e)}

        **Full Traceback:**
        ```
        {error_traceback}
        ```"""

        await cl.Message(content=error_message).send()
