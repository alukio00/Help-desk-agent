
from collections import Counter
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from citywheels import handle_message

load_dotenv(ROOT / ".env")

QUESTIONS_FILE = ROOT / "eval" / "questions.json"
RESULTS_FILE = ROOT / "eval" / "results.md"


def evaluate_case(case, client):
    """Run one evaluation case and check its expected outcome."""

    trace = []

    try:
        answer = handle_message(case["question"], client, tool_trace=trace)

        expected_tools = case["expected_tools"]
        expected_contains = case["expected_contains"]

        tools_passed = Counter(trace) == Counter(expected_tools)


        content_passed = all(
            expected.lower() in answer.lower()
            for expected in expected_contains
        )

        passed = tools_passed and content_passed

        return {
            "id": case["id"],
            "question": case["question"],
            "category": case["category"],
            "passed": passed,
            "expected_tools": expected_tools,
            "actual_tools": trace,
            "expected_contains": expected_contains,
            "answer": answer,
            "error": None,
        }

    except Exception as error:
        return {
            "id": case["id"],
            "question": case["question"],
            "category": case["category"],
            "passed": False,
            "expected_tools": case["expected_tools"],
            "actual_tools": trace,
            "expected_contains": case["expected_contains"],
            "answer": "",
            "error": str(error),
        }


def save_results(results):
    """Save the evaluation report as a Markdown file."""

    total = len(results)
    passed = sum(result["passed"] for result in results)
    failed = total - passed

    pass_rate = (passed / total * 100) if total else 0

    lines = [
        "# CityWheels Agent Evaluation",
        "",
        f"Date: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Total questions: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Pass rate: {pass_rate:.1f}%",
        "",
        "## Individual results",
        "",
        "| ID | Category | Status | Expected tools | Actual tools |",
        "|---|---|---|---|---|",
    ]

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        lines.append(
            f"| {result['id']} "
            f"| {result['category']} "
            f"| {status} "
            f"| {', '.join(result['expected_tools']) or 'None'} "
            f"| {', '.join(result['actual_tools']) or 'None'} |"
        )

    lines.extend(["", "## Detailed results", ""])

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        lines.extend([
            f"### {result['id']} - {status}",
            "",
            f"**Question:** {result['question']}",
            "",
            f"**Expected tools:** {result['expected_tools']}",
            "",
            f"**Actual tools:** {result['actual_tools']}",
            "",
            f"**Expected content:** {result['expected_contains']}",
            "",
            f"**Agent answer:** {result['answer'] or '(empty)'}",
            "",
        ])

        if result["error"]:
            lines.extend([
                f"**Error:** {result['error']}",
                "",
            ])

    RESULTS_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("\n".join(lines[:10]))
    print(f"\nFull report saved to: {RESULTS_FILE}")


def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY")

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        questions = json.load(file)

    client = genai.Client(api_key=api_key)

    results = []

    for case in questions:
        print(f"\nRunning {case['id']}: {case['question']}")

        result = evaluate_case(case, client)
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}: {case['id']}")

        if result["error"]:
            print(f"Error: {result['error']}")

    save_results(results)

    passed = sum(result["passed"] for result in results)

    print(f"\nFinal score: {passed}/{len(results)}")


if __name__ == "__main__":
    main()
