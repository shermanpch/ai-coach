import os

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Data Paths
# Path to the main JSON file with university data
JSON_DATA_PATH = "data/chatbot/peterson_data.json"
# Directory containing markdown files for each university
MARKDOWN_DATA_DIR = "data/chatbot/peterson_documents/"

# ChromaDB Settings
CHROMA_PERSIST_DIR = "chroma-peterson"  # Directory to persist ChromaDB
CHROMA_COLLECTION_NAME = "peterson"  # Name of the collection in ChromaDB

# Embedding Model
# Using Sentence Transformers model - no API key required
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
