import json
from pathlib import Path

from app.evaluation.retrieval_eval import evaluate_retrieval
from app.evaluation.answer_eval import evaluate_answer
from app.rag.rag_qa import ask   # simple RAG answer generator


def main():
    data_path = Path("data/eval_questions.json")
    if not data_path.exists():
        print(f"Evaluation data not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total_recall = 0
    total_precision = 0
    total_mrr = 0
    total_score = 0
    n = len(questions)

    per_question_results = []

    print(f"Evaluating {n} questions...\n")

    for i, q in enumerate(questions, 1):
        question = q["question"]
        relevant_pages = q.get("relevant_pages", [])
        expected_answer = q.get("expected_answer", "")

        # Retrieve and evaluate
        retrieval_metrics = evaluate_retrieval(question, relevant_pages, k=5)
        recall = retrieval_metrics["recall"]
        precision = retrieval_metrics["precision"]
        mrr = retrieval_metrics["mrr"]

        total_recall += recall
        total_precision += precision
        total_mrr += mrr

        # Generate answer (using simple RAG)
        generated_answer = ask(question)

        # Evaluate answer quality
        answer_eval = evaluate_answer(question, expected_answer, generated_answer)
        score = answer_eval["score"]
        total_score += score

        print(f"Q{i}: {question[:60]}...")
        print(f"  Recall@{5}: {recall}, Precision@{5}: {precision:.2f}, MRR: {mrr:.2f}")
        print(f"  Answer score: {score}/5")
        print(f"  Generated: {generated_answer[:100]}...\n")

        # Store full per-question result for the baseline report
        per_question_results.append({
            "question": question,
            "relevant_pages": relevant_pages,
            "expected_answer": expected_answer,
            "generated_answer": generated_answer,
            "recall_at_5": recall,
            "precision_at_5": precision,
            "mrr": mrr,
            "answer_score": score,
        })

    print("\n=== Overall Results ===")
    print(f"Average Recall@{5}: {total_recall/n:.2f}")
    print(f"Average Precision@{5}: {total_precision/n:.2f}")
    print(f"Average MRR: {total_mrr/n:.2f}")
    print(f"Average Answer Score: {total_score/n:.2f}/5")

    # Save results
    results_summary = {
        "average_recall_at_5": total_recall / n,
        "average_precision_at_5": total_precision / n,
        "average_mrr": total_mrr / n,
        "average_answer_score": total_score / n,
        "per_question": per_question_results,
    }

    output_path = Path("experiments/baseline_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print(f"\nSaved baseline results to {output_path}")


if __name__ == "__main__":
    main()