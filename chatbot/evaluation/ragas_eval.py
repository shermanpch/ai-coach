import json
import os
from collections import defaultdict
from statistics import mean, median

from dotenv import load_dotenv
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_openai import ChatOpenAI
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import ContextRelevance

from chatbot.components.retriever import create_self_query_retriever, query_vectorstore
from chatbot.components.vectorstore import get_vectorstore
from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Setup environment (sets project root, ensures logs dir)
PROJECT_ROOT, LOGS_DIR = setup_project_environment()
os.chdir(PROJECT_ROOT)

load_dotenv()
logger = setup_logger(__file__)

# Define Test Questions
TEST_QUESTIONS = [
    "Recommend me a college in Texas where my combined SAT of 1200 or below still fits the mid-range.",
    "Are there any women's colleges in the Northeast that offer a strong neuroscience major?",
    "I need a public university with in-state tuition under $10,000 and merit aid for a 3.5 GPA.",
    "Suggest a school that has an excellent music program and a Division I men's soccer team.",
    "Find colleges offering a computer-science bachelor's that frequently award full-ride scholarships to international students.",
    "Which universities have rolling admissions, accept about a 25 ACT composite, and meet at least 80% of demonstrated financial need?",
    "I prefer a cold climate—recommend a college with varsity skiing and an environmental-studies major.",
    "Point me to a liberal-arts college with a 10:1 or better student-faculty ratio, no application fee, and test-optional admissions.",
    "What historically Black colleges or universities have a nursing program and typically admit students around a 3.0 GPA?",
    "Are there any schools near a large city that offer associate degrees in culinary arts?",
    "Suggest an engineering school known for strong co-op or paid internship programs, especially in ABET-accredited mechanical engineering.",
    "Recommend an East-Coast college that has both marine biology and a sailing team.",
]


def calculate_retrieval_metrics(detailed_retrieval_data: list[dict]) -> dict:
    """
    Calculate retrieval metrics from detailed retrieval data.

    Args:
        detailed_retrieval_data: List of detailed retrieval entries

    Returns:
        dict: Dictionary containing various retrieval metrics
    """
    metrics = {}

    # Filter out error entries
    valid_entries = [
        d for d in detailed_retrieval_data if d.get("document_id") != "ERROR"
    ]

    # Basic statistics
    metrics["total_retrievals"] = len(detailed_retrieval_data)
    metrics["successful_retrievals"] = len(valid_entries)
    metrics["failed_retrievals"] = len(detailed_retrieval_data) - len(valid_entries)
    metrics["success_rate"] = (
        len(valid_entries) / len(detailed_retrieval_data)
        if detailed_retrieval_data
        else 0
    )

    if not valid_entries:
        return metrics

    # Similarity score statistics
    similarity_scores = []
    for entry in valid_entries:
        score = entry.get("similarity_score")
        if isinstance(score, int | float) and score != "N/A":
            similarity_scores.append(score)

    if similarity_scores:
        metrics["similarity_scores"] = {
            "count": len(similarity_scores),
            "mean": mean(similarity_scores),
            "median": median(similarity_scores),
            "min": min(similarity_scores),
            "max": max(similarity_scores),
            "scores": similarity_scores,
        }

    # Context relevance score statistics (if available)
    relevance_scores = []
    for entry in valid_entries:
        score = entry.get("context_relevance_score")
        if isinstance(score, int | float):
            relevance_scores.append(score)

    if relevance_scores:
        metrics["context_relevance_scores"] = {
            "count": len(relevance_scores),
            "mean": mean(relevance_scores),
            "median": median(relevance_scores),
            "min": min(relevance_scores),
            "max": max(relevance_scores),
            "scores": relevance_scores,
        }

    # Question-level statistics
    questions_stats = defaultdict(list)
    for entry in valid_entries:
        question_idx = entry.get("question_index")
        if question_idx:
            questions_stats[question_idx].append(entry)

    metrics["questions_stats"] = {
        "total_questions": len(questions_stats),
        "avg_docs_per_question": (
            mean([len(docs) for docs in questions_stats.values()])
            if questions_stats
            else 0
        ),
        "questions_with_results": len(
            [q for q, docs in questions_stats.items() if docs]
        ),
    }

    # University diversity
    unique_universities = {
        entry.get("university_name")
        for entry in valid_entries
        if entry.get("university_name") and entry.get("university_name") != "N/A"
    }
    metrics["university_diversity"] = {
        "unique_universities_count": len(unique_universities),
        "universities": list(unique_universities),
    }

    # Filter usage statistics
    with_filters = len(
        [
            d
            for d in valid_entries
            if d.get("metadata_filter") not in ["No filter", "ERROR"]
        ]
    )
    metrics["filter_usage"] = {
        "with_filters": with_filters,
        "without_filters": len(valid_entries) - with_filters,
        "filter_usage_rate": with_filters / len(valid_entries) if valid_entries else 0,
    }

    return metrics


def append_relevance_scores_to_detailed_data(
    detailed_retrieval_data: list[dict], ragas_result
) -> list[dict]:
    """
    Append RAGAS context relevance scores to each document in detailed retrieval data.

    Args:
        detailed_retrieval_data: List of detailed retrieval entries
        ragas_result: RAGAS evaluation result object

    Returns:
        Updated detailed retrieval data with relevance scores
    """
    if not hasattr(ragas_result, "scores") or not ragas_result.scores:
        logger.warning("No RAGAS scores found to append")
        return detailed_retrieval_data

    # Create a mapping of questions to their relevance scores
    question_scores = {}
    for i, score_dict in enumerate(ragas_result.scores):
        if isinstance(score_dict, dict) and "nv_context_relevance" in score_dict:
            # Question index is i+1 since we start from 1 in the data
            question_scores[i + 1] = score_dict["nv_context_relevance"]

    logger.info(f"Mapping relevance scores for {len(question_scores)} questions")

    # Group documents by question to assign the same relevance score to all docs from the same question
    updated_data = []
    for entry in detailed_retrieval_data:
        updated_entry = entry.copy()
        question_idx = entry.get("question_index")

        if question_idx in question_scores:
            updated_entry["context_relevance_score"] = question_scores[question_idx]
            logger.debug(
                f"Added relevance score {question_scores[question_idx]} to document {entry.get('document_id', 'N/A')} for question {question_idx}"
            )
        else:
            updated_entry["context_relevance_score"] = None
            logger.debug(f"No relevance score available for question {question_idx}")

        updated_data.append(updated_entry)

    return updated_data


def prepare_evaluation_data(
    retriever, questions: list[str]
) -> tuple[list[dict], list[dict]]:
    """
    Prepare evaluation data in the format expected by RAGAS EvaluationDataset.
    Also collect detailed retrieval information for each document.

    Returns:
        tuple: (ragas_dataset, detailed_retrieval_data)
        - ragas_dataset: list of dicts with keys: user_input, retrieved_contexts, response
        - detailed_retrieval_data: list of dicts with detailed retrieval info per document
    """
    dataset = []
    detailed_retrieval_data = []
    logger.info(f"Preparing evaluation data for {len(questions)} questions...")

    for i, query in enumerate(questions):
        logger.info(f"Processing question {i + 1}/{len(questions)}: '{query[:70]}...'")
        try:
            # Get the structured query to capture the metadata filter
            structured_query = retriever.query_constructor.invoke({"query": query})
            metadata_filter = getattr(structured_query, "filter", None)
            search_query = getattr(structured_query, "query", query)

            logger.info(f"Structured query: {structured_query}")

            # Retrieve contexts using the retriever
            retrieved_docs = retriever.invoke(query)
            retrieved_contexts = [doc.page_content for doc in retrieved_docs]

            # Try to get similarity scores by using the vectorstore directly
            try:
                # Use the existing query_vectorstore function which handles filters properly

                if metadata_filter:
                    # Translate the LangChain filter to Chroma format using the same translator
                    translator = ChromaTranslator()
                    # visit_structured_query returns (query, filter) tuple
                    translated_query, chroma_filter = translator.visit_structured_query(
                        structured_query
                    )

                    # Extract the actual filter from the result
                    actual_filter = (
                        chroma_filter.get("filter")
                        if isinstance(chroma_filter, dict)
                        else chroma_filter
                    )

                    docs_with_scores = query_vectorstore(
                        vectorstore=retriever.vectorstore,
                        query_text=search_query,
                        k=len(retrieved_docs),
                        metadata_filter=actual_filter,
                        with_scores=True,
                    )
                else:
                    docs_with_scores = query_vectorstore(
                        vectorstore=retriever.vectorstore,
                        query_text=search_query,
                        k=len(retrieved_docs),
                        with_scores=True,
                    )
                # Create a mapping of document content to scores
                score_map = {doc.page_content: score for doc, score in docs_with_scores}
            except Exception as score_error:
                logger.warning(f"Could not retrieve similarity scores: {score_error}")
                score_map = {}

            if not retrieved_contexts:
                logger.warning(f"No contexts retrieved for question: {query}")
                retrieved_contexts = []

            response = "PLACEHOLDER"

            # Store RAGAS dataset entry
            dataset.append(
                {
                    "user_input": query,
                    "retrieved_contexts": retrieved_contexts,
                    "response": response,
                }
            )

            # Store detailed retrieval information for each document
            for doc_idx, doc in enumerate(retrieved_docs):
                document_id = doc.metadata.get("document_id", "N/A")
                university_name = doc.metadata.get("university_name", "N/A")
                similarity_score = score_map.get(doc.page_content, "N/A")

                detailed_entry = {
                    "question_index": i + 1,
                    "user_input": query,
                    "search_query": search_query,
                    "metadata_filter": (
                        str(metadata_filter) if metadata_filter else "No filter"
                    ),
                    "document_rank": doc_idx + 1,
                    "document_id": document_id,
                    "university_name": university_name,
                    "similarity_score": similarity_score,
                    "document_metadata": doc.metadata,
                    "content_preview": (
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    ),
                }
                detailed_retrieval_data.append(detailed_entry)

            logger.info(
                f"Retrieved {len(retrieved_contexts)} contexts for question {i + 1}."
            )

        except Exception as e:
            logger.error(f"Error processing question '{query}': {e}")
            # Add entry with empty contexts for failed retrievals
            dataset.append(
                {
                    "user_input": query,
                    "retrieved_contexts": [],
                    "response": f"Unable to retrieve information for: {query}",
                }
            )

            # Add error entry to detailed data
            detailed_entry = {
                "question_index": i + 1,
                "user_input": query,
                "search_query": "ERROR",
                "metadata_filter": "ERROR",
                "document_rank": 0,
                "document_id": "ERROR",
                "university_name": "ERROR",
                "similarity_score": "ERROR",
                "document_metadata": {},
                "content_preview": f"Error: {str(e)}",
                "error": str(e),
            }
            detailed_retrieval_data.append(detailed_entry)

    logger.info("Evaluation dataset prepared.")
    return dataset, detailed_retrieval_data


if __name__ == "__main__":
    logger.info("Starting RAGAS evaluation for retrieval system...")

    # Load vectorstore
    db_vectorstore = get_vectorstore()
    logger.info("Vectorstore loaded.")

    # Create retriever
    retriever = create_self_query_retriever(vectorstore=db_vectorstore, k=3)
    logger.info("Self-query retriever created.")

    # Check if detailed retrieval data already exists
    detailed_retrieval_path = (
        PROJECT_ROOT / "chatbot" / "evaluation" / "detailed_retrieval_data.json"
    )

    if detailed_retrieval_path.exists():
        logger.info("Loading existing detailed retrieval data...")
        with open(detailed_retrieval_path) as f:
            detailed_retrieval_data = json.load(f)
        logger.info(
            f"Loaded {len(detailed_retrieval_data)} retrieval entries from existing data."
        )

        # Create dataset from existing data for RAGAS evaluation
        dataset_list = []
        questions_data = defaultdict(list)

        # Group by question
        for entry in detailed_retrieval_data:
            if entry.get("document_id") != "ERROR":
                questions_data[entry["user_input"]].append(entry["content_preview"])

        # Create dataset entries
        for question, contexts in questions_data.items():
            dataset_list.append(
                {
                    "user_input": question,
                    "retrieved_contexts": contexts,
                    "response": "PLACEHOLDER",
                }
            )
    else:
        # Prepare evaluation dataset
        dataset_list, detailed_retrieval_data = prepare_evaluation_data(
            retriever, TEST_QUESTIONS
        )
        if not dataset_list:
            logger.error("Failed to prepare evaluation dataset. Exiting.")
            exit(1)

        # Save detailed retrieval data
        with open(detailed_retrieval_path, "w") as f:
            json.dump(detailed_retrieval_data, f, indent=2, default=str)
        logger.info(f"Detailed retrieval data saved to: {detailed_retrieval_path}")

    # Create EvaluationDataset from the list
    evaluation_dataset = EvaluationDataset.from_list(dataset_list)
    logger.info(f"Evaluation dataset created with {len(dataset_list)} samples.")

    # Configure RAGAS LLM (using OpenRouter)
    ragas_llm_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    logger.info(f"Using RAGAS LLM: {ragas_llm_model}")

    langchain_llm_for_ragas = ChatOpenAI(
        model=ragas_llm_model,
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_EVAL_REF", "http://localhost:8000"),
            "X-Title": os.getenv("OPENROUTER_TITLE_EVAL", "AI College Coach RAGAS"),
        },
        max_retries=3,
    )

    # Wrap the LangChain LLM for RAGAS compatibility
    evaluator_llm = LangchainLLMWrapper(langchain_llm_for_ragas)

    # Define metrics for evaluation
    # Using metrics that don't require reference answers
    metrics_to_evaluate = [
        ContextRelevance(),  # Measures how relevant the retrieved context is to the question
    ]

    logger.info(
        f"Metrics to evaluate: {[type(m).__name__ for m in metrics_to_evaluate]}"
    )

    # Run RAGAS evaluation
    logger.info("Starting RAGAS evaluation process...")
    try:
        result = evaluate(
            dataset=evaluation_dataset,
            metrics=metrics_to_evaluate,
            llm=evaluator_llm,
            raise_exceptions=False,  # Continue evaluation even if some items fail
        )
        logger.info("RAGAS evaluation finished.")

        # Display and save results
        if result:
            logger.info("=== RAGAS EVALUATION RESULTS ===")
            logger.info(f"RAGAS Result: {result}")

            # Append relevance scores to detailed retrieval data
            updated_detailed_data = append_relevance_scores_to_detailed_data(
                detailed_retrieval_data, result
            )

            # Save updated detailed retrieval data with relevance scores
            with open(detailed_retrieval_path, "w") as f:
                json.dump(updated_detailed_data, f, indent=2, default=str)
            logger.info(
                f"Updated detailed retrieval data with relevance scores saved to: {detailed_retrieval_path}"
            )

            # Calculate and display retrieval metrics from updated detailed data
            retrieval_metrics = calculate_retrieval_metrics(updated_detailed_data)
            logger.info("=== RETRIEVAL METRICS FROM DETAILED DATA ===")
            logger.info(f"Total retrievals: {retrieval_metrics['total_retrievals']}")
            logger.info(
                f"Successful retrievals: {retrieval_metrics['successful_retrievals']}"
            )
            logger.info(f"Failed retrievals: {retrieval_metrics['failed_retrievals']}")
            logger.info(f"Success rate: {retrieval_metrics['success_rate']:.2%}")

            if "similarity_scores" in retrieval_metrics:
                sim_stats = retrieval_metrics["similarity_scores"]
                logger.info(
                    f"Similarity scores - Count: {sim_stats['count']}, Mean: {sim_stats['mean']:.4f}, Median: {sim_stats['median']:.4f}"
                )
                logger.info(
                    f"Similarity scores - Min: {sim_stats['min']:.4f}, Max: {sim_stats['max']:.4f}"
                )

            if "context_relevance_scores" in retrieval_metrics:
                rel_stats = retrieval_metrics["context_relevance_scores"]
                logger.info(
                    f"Context relevance scores - Count: {rel_stats['count']}, Mean: {rel_stats['mean']:.4f}, Median: {rel_stats['median']:.4f}"
                )
                logger.info(
                    f"Context relevance scores - Min: {rel_stats['min']:.4f}, Max: {rel_stats['max']:.4f}"
                )

            q_stats = retrieval_metrics["questions_stats"]
            logger.info(f"Questions processed: {q_stats['total_questions']}")
            logger.info(
                f"Average documents per question: {q_stats['avg_docs_per_question']:.2f}"
            )

            univ_stats = retrieval_metrics["university_diversity"]
            logger.info(
                f"Unique universities found: {univ_stats['unique_universities_count']}"
            )

            filter_stats = retrieval_metrics["filter_usage"]
            logger.info(
                f"Queries with metadata filters: {filter_stats['with_filters']} ({filter_stats['filter_usage_rate']:.2%})"
            )
            logger.info(f"Queries without filters: {filter_stats['without_filters']}")

            # Print RAGAS summary statistics
            logger.info("=== RAGAS SUMMARY STATISTICS ===")
            if hasattr(result, "scores"):
                # Handle different score formats
                if isinstance(result.scores, dict):
                    # If scores is a dictionary
                    for key, value in result.scores.items():
                        if isinstance(value, int | float):
                            logger.info(f"{key}: {value:.4f}")
                        elif isinstance(value, list) and value:
                            mean_score = sum(value) / len(value)
                            logger.info(f"{key}: {mean_score:.4f}")
                elif isinstance(result.scores, list):
                    # Calculate overall mean from individual question scores
                    all_scores = []
                    for score_dict in result.scores:
                        if (
                            isinstance(score_dict, dict)
                            and "nv_context_relevance" in score_dict
                        ):
                            all_scores.append(score_dict["nv_context_relevance"])
                    if all_scores:
                        mean_relevance = sum(all_scores) / len(all_scores)
                        logger.info(f"Overall Context Relevance: {mean_relevance:.4f}")
                        logger.info(f"Individual scores: {all_scores}")
                else:
                    logger.info(f"Scores: {result.scores}")

            # Also check for individual metric attributes (common in RAGAS)
            for attr_name in dir(result):
                if not attr_name.startswith("_") and attr_name != "scores":
                    try:
                        attr_value = getattr(result, attr_name)
                        if isinstance(attr_value, int | float) and 0 <= attr_value <= 1:
                            logger.info(f"{attr_name}: {attr_value:.4f}")
                    except Exception:
                        pass
        else:
            logger.warning("RAGAS evaluation did not return any results.")

    except Exception as e:
        logger.error(f"Error during RAGAS evaluation: {e}")
        raise
