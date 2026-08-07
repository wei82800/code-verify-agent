import os
from dotenv import load_dotenv

load_dotenv()

# API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-haiku-4-5-20251001"  # Start cheap, switch to sonnet for final run
TEMPERATURE = 0.7

# Agent configuration
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Benchmark configuration
BENCHMARK_SIZE = 50  # Use subset for real benchmark
BENCHMARK_SOURCE = "humaneval"  # Real benchmark for final results

# Output paths
RESULTS_DIR = "results"
LOGS_DIR = "logs"
