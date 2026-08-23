import argparse
import json
from pathlib import Path

from app.evaluation.retrieval_eval import evaluate_retrieval
from app.evaluation.answer_eval import evaluate_answer
from app.rag.rag_qa import ask
from app.rag.vector_store import search
from app.agents.research_agent import run_full_pipeline   # new import


K = 5


def inspect_retrieval(question):
    """Print the top-k retrieved chunks for manual inspection."""
    print(f"\n{'=' * 80}")
    print(f"QUESTION: {question}")
    print(f"{'=' * 80}")

    results = search(question, k=K)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for rank, (doc, meta, dist) in enumerate(
        zip(documents, metadatas, distances), 1
    ):
        page = meta.get("page", "Unknown")

        print(f"\n--- Rank {rank} | Page {page} | Distance {dist:.3f} ---")
        print(doc[:500].replace("\n", " "))

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate ResearchPilot performance."
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="rag",
        choices=["rag", "pipeline"],
        help="Answer generation mode: 'rag' (simple) or 'pipeline' (multi-agent).",
    )

    parser.add_argument(
        "--inspect-failures",
        action="store_true",
        help="Print top-5 retrieved chunks for failed questions.",
    )

    parser.add_argument(
        "--answer-threshold",
        type=float,
        default=3.0,
        help="Inspect questions with answer score below this threshold.",
    )

    args = parser.parse_args()

    data_path = Path("data/eval_questions.json")

    if not data_path.exists():
        print(f"Evaluation data not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if not questions:
        print("No evaluation questions found.")
        return

    print(f"Evaluating {len(questions)} questions in '{args.mode}' mode...\n")

    total_recall = 0
    total_precision = 0
    total_mrr = 0
    total_score = 0

    n = len(questions)

    per_question_results = []
    failed_questions = []

    for i, q in enumerate(questions, 1):
        question = q["question"]
        relevant_pages = q.get("relevant_pages", [])
        expected_answer = q.get("expected_answer", "")

        # ---------------------------------------------------------
        # Retrieval evaluation (same for both modes)
        # ---------------------------------------------------------
        retrieval_metrics = evaluate_retrieval(
            question,
            relevant_pages,
            k=K,
        )

        recall = retrieval_metrics["recall"]
        precision = retrieval_metrics["precision"]
        mrr = retrieval_metrics["mrr"]

        total_recall += recall
        total_precision += precision
        total_mrr += mrr

        # ---------------------------------------------------------
        # Answer generation (depends on mode)
        # ---------------------------------------------------------
        if args.mode == "pipeline":
            pipeline_result = run_full_pipeline(question)
            generated_answer = pipeline_result.get("answer", "")
        else:
            generated_answer = ask(question)

        # ---------------------------------------------------------
        # Answer evaluation
        # ---------------------------------------------------------
        answer_eval = evaluate_answer(
            question,
            expected_answer,
            generated_answer,
        )

        score = answer_eval["score"]
        total_score += score

        print(f"Q{i}: {question[:60]}...")
        print(
            f"  Recall@{K}: {recall:.2f}, "
            f"Precision@{K}: {precision:.2f}, "
            f"MRR: {mrr:.2f}"
        )
        print(f"  Answer score: {score}/5")
        print(f"  Generated: {generated_answer[:100]}...\n")

        # ---------------------------------------------------------
        # Store complete result
        # ---------------------------------------------------------
        result = {
            "question": question,
            "relevant_pages": relevant_pages,
            "expected_answer": expected_answer,
            "generated_answer": generated_answer,
            "recall_at_5": recall,
            "precision_at_5": precision,
            "mrr": mrr,
            "answer_score": score,
        }

        per_question_results.append(result)

        # ---------------------------------------------------------
        # Identify questions worth manually inspecting
        # ---------------------------------------------------------
        if (
            recall < 1.0
            or mrr < 1.0
            or score < args.answer_threshold
        ):
            failed_questions.append(result)

    # -------------------------------------------------------------
    # Overall results
    # -------------------------------------------------------------
    average_recall = total_recall / n
    average_precision = total_precision / n
    average_mrr = total_mrr / n
    average_score = total_score / n

    print("\n=== Overall Results ===")
    print(f"Average Recall@{K}: {average_recall:.2f}")
    print(f"Average Precision@{K}: {average_precision:.2f}")
    print(f"Average MRR: {average_mrr:.2f}")
    print(f"Average Answer Score: {average_score:.2f}/5")

    # -------------------------------------------------------------
    # Manual retrieval inspection
    # -------------------------------------------------------------
    if args.inspect_failures:
        print("\n")
        print("=" * 80)
        print("MANUAL RETRIEVAL INSPECTION")
        print("=" * 80)

        if not failed_questions:
            print("\nNo failed/low-scoring questions found.")
        else:
            print(
                f"\nInspecting {len(failed_questions)} "
                "failed/low-scoring questions..."
            )

            for result in failed_questions:
                inspect_retrieval(result["question"])

    # -------------------------------------------------------------
    # Save results
    # -------------------------------------------------------------
    results_summary = {
        "average_recall_at_5": average_recall,
        "average_precision_at_5": average_precision,
        "average_mrr": average_mrr,
        "average_answer_score": average_score,
        "per_question": per_question_results,
    }

    output_path = Path(f"experiments/baseline_{args.mode}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\nSaved results to {output_path}")


if __name__ == "__main__":
    main()