#!/usr/bin/env python3
"""Main entry point for code generation experiments."""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime

import config
from agent import CodeGenerationAgent
from benchmark_loader import BenchmarkLoader


# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_baseline_experiment(agent: CodeGenerationAgent, tasks: list, output_dir: Path):
    """Run single-shot generation (no verification)."""
    logger.info("Running BASELINE experiment (single-shot, no verification)...")
    results = []
    success_count = 0

    for i, task in enumerate(tasks):
        logger.info(f"[{i+1}/{len(tasks)}] Task {task.task_id}")
        result = agent.run_experiment(task, use_verification=False)
        results.append(result)
        if result["success"]:
            success_count += 1
            logger.info(f"  ✓ PASSED")
        else:
            logger.info(f"  ✗ FAILED")

    # Save results
    output_file = output_dir / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump({
            "experiment": "baseline",
            "model": config.MODEL,
            "total_tasks": len(tasks),
            "passed": success_count,
            "success_rate": success_count / len(tasks),
            "results": results
        }, f, indent=2)

    logger.info(f"\nBaseline Results: {success_count}/{len(tasks)} ({100*success_count/len(tasks):.1f}%)")
    return results


def run_verification_experiment(agent: CodeGenerationAgent, tasks: list, output_dir: Path):
    """Run with verify-retry loop."""
    logger.info("Running VERIFICATION experiment (with retry loop)...")
    results = []
    success_count = 0
    total_retries = 0

    for i, task in enumerate(tasks):
        logger.info(f"[{i+1}/{len(tasks)}] Task {task.task_id}")
        result = agent.run_experiment(task, use_verification=True)
        results.append(result)
        if result["success"]:
            success_count += 1
            total_retries += result["attempts"]
            logger.info(f"  ✓ PASSED (attempts: {result['attempts'] + 1})")
        else:
            total_retries += result["attempts"]
            logger.info(f"  ✗ FAILED after {result['attempts'] + 1} attempts")

    # Save results
    output_file = output_dir / f"verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump({
            "experiment": "verification",
            "model": config.MODEL,
            "max_retries": config.MAX_RETRIES,
            "total_tasks": len(tasks),
            "passed": success_count,
            "success_rate": success_count / len(tasks),
            "avg_attempts": total_retries / len(tasks) if tasks else 0,
            "results": results
        }, f, indent=2)

    logger.info(f"\nVerification Results: {success_count}/{len(tasks)} ({100*success_count/len(tasks):.1f}%)")
    logger.info(f"Average attempts: {total_retries / len(tasks):.2f}")
    return results


def compare_experiments(baseline_results: list, verification_results: list):
    """Compare and print ablation study results."""
    logger.info("\n" + "="*60)
    logger.info("ABLATION STUDY SUMMARY")
    logger.info("="*60)

    baseline_success = sum(1 for r in baseline_results if r["success"])
    verification_success = sum(1 for r in verification_results if r["success"])
    total = len(baseline_results)

    baseline_rate = baseline_success / total * 100
    verification_rate = verification_success / total * 100
    improvement = verification_rate - baseline_rate

    logger.info(f"Baseline (no verification):        {baseline_success}/{total} ({baseline_rate:.1f}%)")
    logger.info(f"With verification loop:            {verification_success}/{total} ({verification_rate:.1f}%)")
    logger.info(f"Improvement:                       +{improvement:.1f}%")

    # Identify tasks where verification helped
    helped = 0
    for b, v in zip(baseline_results, verification_results):
        if not b["success"] and v["success"]:
            helped += 1

    logger.info(f"Tasks improved by verification:    {helped}/{total - baseline_success}")
    logger.info("="*60)


def main():
    # Create output directories
    results_dir = Path(config.RESULTS_DIR)
    results_dir.mkdir(exist_ok=True)

    # Load tasks
    logger.info(f"Loading {config.BENCHMARK_SIZE} benchmark tasks...")
    if config.BENCHMARK_SOURCE == "mock":
        tasks = BenchmarkLoader.create_mock_tasks(config.BENCHMARK_SIZE)
    elif config.BENCHMARK_SOURCE == "humaneval":
        try:
            tasks = BenchmarkLoader.load_humaneval_subset(config.BENCHMARK_SIZE)
        except Exception as e:
            logger.warning(f"Failed to load HumanEval: {e}, using mock tasks instead")
            tasks = BenchmarkLoader.create_mock_tasks(config.BENCHMARK_SIZE)
    else:
        tasks = BenchmarkLoader.create_mock_tasks(config.BENCHMARK_SIZE)

    logger.info(f"Loaded {len(tasks)} tasks")

    # Initialize agent
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Please set it in .env file")
        sys.exit(1)

    agent = CodeGenerationAgent(
        model=config.MODEL,
        api_key=config.ANTHROPIC_API_KEY,
        temperature=config.TEMPERATURE
    )

    # Run experiments
    logger.info(f"Using model: {config.MODEL}")
    baseline_results = run_baseline_experiment(agent, tasks, results_dir)
    verification_results = run_verification_experiment(agent, tasks, results_dir)

    # Compare results
    compare_experiments(baseline_results, verification_results)

    logger.info(f"\nResults saved to: {results_dir}")


if __name__ == "__main__":
    main()
