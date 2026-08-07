#!/usr/bin/env python3
"""Analyze failure patterns from results."""

import json
from pathlib import Path
from collections import defaultdict


def analyze_results(baseline_file: str, verification_file: str):
    """Analyze and compare baseline vs verification results."""

    with open(baseline_file) as f:
        baseline = json.load(f)

    with open(verification_file) as f:
        verification = json.load(f)

    print("\n" + "="*70)
    print("FAILURE ANALYSIS - HumanEval Benchmark")
    print("="*70)

    # Extract results
    baseline_results = {r["task_id"]: r for r in baseline["results"]}
    verification_results = {r["task_id"]: r for r in verification["results"]}

    # Categorize failures
    baseline_failures = [r for r in baseline["results"] if not r["success"]]
    verification_failures = [r for r in verification["results"] if not r["success"]]

    # Tasks improved by verification
    improved = []
    for task_id in baseline_results:
        if not baseline_results[task_id]["success"] and verification_results[task_id]["success"]:
            improved.append(task_id)

    print(f"\n📊 SUMMARY")
    print(f"  Baseline failures:     {len(baseline_failures)}/{len(baseline['results'])} ({100*len(baseline_failures)/len(baseline['results']):.1f}%)")
    print(f"  Verification failures: {len(verification_failures)}/{len(verification['results'])} ({100*len(verification_failures)/len(verification['results']):.1f}%)")
    print(f"  Tasks rescued:         {len(improved)}/{len(baseline_failures)} ({100*len(improved)/len(baseline_failures):.1f}% of failures)")

    print(f"\n🔧 RESCUED TASKS (by verification loop):")
    for task_id in improved[:5]:  # Show top 5
        baseline_error = baseline_results[task_id]["details"][:100]
        attempts = verification_results[task_id]["attempts"]
        print(f"  ✓ {task_id} (attempts: {attempts+1})")
        print(f"    Error: {baseline_error}...")

    print(f"\n❌ TASKS STILL FAILING (even with verification):")
    for r in verification_failures[:5]:  # Show top 5
        task_id = r["task_id"]
        error = r["details"][:150]
        print(f"  ✗ {task_id}")
        print(f"    Error: {error}...")

    # Error pattern analysis
    print(f"\n📈 ERROR PATTERNS IN BASELINE FAILURES:")
    error_patterns = defaultdict(int)

    for r in baseline_failures:
        details = r["details"].lower()
        if "nameerror" in details:
            error_patterns["NameError (function name mismatch)"] += 1
        elif "typeerror" in details:
            error_patterns["TypeError (logic error)"] += 1
        elif "collected 0 items / 1 error" in details:
            error_patterns["Collection Error (syntax/import)"] += 1
        elif "not defined" in details:
            error_patterns["Not Defined (missing function)"] += 1
        else:
            error_patterns["Other"] += 1

    for error_type, count in sorted(error_patterns.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(baseline_failures)
        rescue_rate = sum(1 for task_id in improved if error_type.split()[0].lower() in baseline_results[task_id]["details"].lower()) / max(count, 1)
        print(f"  {error_type}: {count} ({pct:.1f}%)")

    print("\n" + "="*70)
    print(f"📝 Full results saved to JSON files")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Find latest result files
    results_dir = Path("results")
    json_files = sorted(results_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if len(json_files) >= 2:
        # Assume latest verification and baseline
        verification_file = json_files[0]
        baseline_file = json_files[1]

        print(f"Analyzing: {baseline_file.name} vs {verification_file.name}")
        analyze_results(str(baseline_file), str(verification_file))
    else:
        print("No result files found. Run main.py first.")
