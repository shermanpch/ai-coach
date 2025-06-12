import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document


def get_git_root():
    """Get the root directory of the git repository"""
    try:
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .strip()
            .decode("utf-8")
        )
        return Path(git_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Get the project root using git
PROJECT_ROOT = get_git_root()
if PROJECT_ROOT is None:
    print("Error: Not in a git repository or git not found")
    sys.exit(1)

# Change to project root and add to Python path
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from chatbot.components.vectorstore import (
    add_documents_to_vectorstore,
    delete_vectorstore,
    get_vectorstore,
    get_vectorstore_stats,
)
from tests.test_logger import (
    log_metrics,
    log_test_result,
    log_test_step,
    setup_test_logger,
)


class TestVectorstore(unittest.TestCase):
    """Simple test for vectorstore functionality with logging"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        # Set up logger
        self.logger = setup_test_logger("vectorstore")

        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.logger.info(f"Created temporary test directory: {self.test_dir}")

        # Patch the config to use our test directory
        import chatbot.config as config

        self.original_persist_dir = config.CHROMA_PERSIST_DIR
        config.CHROMA_PERSIST_DIR = self.test_dir
        self.logger.info(f"Configured test database path: {self.test_dir}")

    def tearDown(self):
        """Clean up after each test method"""
        # Restore original config
        import chatbot.config as config

        config.CHROMA_PERSIST_DIR = self.original_persist_dir
        self.logger.info("Restored original config")

        # Clean up test database directory
        if os.path.exists(self.test_dir):
            import shutil

            shutil.rmtree(self.test_dir)
            self.logger.info(f"Cleaned up test directory: {self.test_dir}")

    def test_add_documents_and_check_progress(self):
        """Test adding documents and checking progress with detailed logging"""
        test_start_time = datetime.now()

        try:
            log_test_step(self.logger, 1, "Creating initial test documents")

            # Create initial test documents
            initial_docs = [
                Document(
                    page_content="Stanford University is a private research university in California.",
                    metadata={
                        "university_name": "Stanford University",
                        "state": "California",
                        "city": "Stanford",
                    },
                ),
                Document(
                    page_content="Georgia Tech is a public research university in Atlanta.",
                    metadata={
                        "university_name": "Georgia Institute of Technology",
                        "state": "Georgia",
                        "city": "Atlanta",
                    },
                ),
            ]

            self.logger.info(f"Created {len(initial_docs)} initial documents")

            log_test_step(self.logger, 2, "Creating vectorstore with initial documents")
            vectorstore = get_vectorstore(documents=initial_docs, recreate=True)

            # Check initial stats
            stats = get_vectorstore_stats(vectorstore)
            self.logger.info(f"Initial document count: {stats['document_count']}")
            self.assertEqual(stats["document_count"], 2)

            log_test_step(self.logger, 3, "Creating additional documents")

            # Add more documents
            additional_docs = [
                Document(
                    page_content="MIT is a prestigious university in Massachusetts known for technology.",
                    metadata={
                        "university_name": "Massachusetts Institute of Technology",
                        "state": "Massachusetts",
                        "city": "Cambridge",
                    },
                ),
                Document(
                    page_content="UC Berkeley is a public research university in California.",
                    metadata={
                        "university_name": "UC Berkeley",
                        "state": "California",
                        "city": "Berkeley",
                    },
                ),
            ]

            self.logger.info(f"Created {len(additional_docs)} additional documents")

            log_test_step(self.logger, 4, "Adding documents to vectorstore")
            add_documents_to_vectorstore(vectorstore, additional_docs)

            # Check updated stats
            updated_stats = get_vectorstore_stats(vectorstore)
            self.logger.info(
                f"Updated document count: {updated_stats['document_count']}"
            )
            self.assertEqual(updated_stats["document_count"], 4)

            log_test_step(self.logger, 5, "Testing semantic search functionality")

            # Test search to verify documents are accessible
            results = vectorstore.similarity_search("university in California", k=3)
            self.logger.info(
                f"Found {len(results)} results for 'university in California'"
            )

            california_unis = [
                r for r in results if r.metadata.get("state") == "California"
            ]
            self.logger.info(f"California universities found: {len(california_unis)}")

            # Verify we can find California universities
            self.assertGreater(len(california_unis), 0)

            log_test_step(self.logger, 6, "Testing metadata filtering")

            # Test metadata filtering
            georgia_results = vectorstore.similarity_search(
                "university", k=5, filter={"state": "Georgia"}
            )
            self.logger.info(f"Found {len(georgia_results)} universities in Georgia")
            self.assertEqual(len(georgia_results), 1)
            self.assertEqual(georgia_results[0].metadata["state"], "Georgia")

            log_test_step(self.logger, 7, "Testing vectorstore deletion")

            # Test deletion
            result = delete_vectorstore(self.test_dir)
            self.logger.info(f"Deletion successful: {result}")
            self.assertTrue(result)

            # Verify directory was deleted
            self.assertFalse(os.path.exists(self.test_dir))
            self.logger.info("Vectorstore directory successfully removed")

            # Calculate test duration
            test_duration = (datetime.now() - test_start_time).total_seconds()

            # Log test metrics
            test_metrics = {
                "initial_documents": len(initial_docs),
                "additional_documents": len(additional_docs),
                "total_documents": updated_stats["document_count"],
                "search_results_count": len(results),
                "california_universities_found": len(california_unis),
                "georgia_universities_found": len(georgia_results),
                "test_duration_seconds": round(test_duration, 2),
                "embedding_model": updated_stats.get("embedding_model", "unknown"),
                "vectorstore_deleted": result,
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "vectorstore_functionality",
                True,
                "All operations completed successfully",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "vectorstore_functionality", False, str(e))
            raise


if __name__ == "__main__":
    unittest.main()
