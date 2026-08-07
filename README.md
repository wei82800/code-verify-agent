# Code Verification Agent - Day 1 Scaffold

## Overview

A Python project demonstrating **self-verification loops for code generation**. The core idea: compare single-shot code generation (baseline) against a verify-retry loop where the agent fixes code based on test failures.

**Key Deliverable**: Quantified benchmark showing how much self-verification improves success rate.

## Architecture

```
code-verify-agent/
├── config.py              # Configuration (model, API key, parameters)
├── verifier.py            # CodeVerifier: runs tests in isolated subprocess
├── agent.py               # CodeGenerationAgent: single-shot + retry loop logic
├── benchmark_loader.py    # Load HumanEval+/MBPP+ or mock tasks
├── main.py               # Entry point: runs both experiments + comparison
├── results/              # Output JSON files with detailed results
└── .env                  # Your API key (create from .env.example)
```

## Installation

1. Clone/create project structure above
2. Create `.env` from `.env.example` and add your Anthropic API key:
   ```bash
   cp .env.example .env
   # Edit .env and add ANTHROPIC_API_KEY
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Run with Mock Tasks (No Internet, Fast)
Best for Day 1 testing — no dataset download needed:

```bash
python main.py
```

By default uses 10 mock coding tasks (sum, prime check, palindrome, etc.). You'll see:
- **Baseline** results: single-shot generation success rate
- **Verification** results: retry loop success rate  
- **Comparison**: improvement percentage and task-by-task details

### Run with Real Benchmark (Slower, More Realistic)
Edit `config.py`:
```python
BENCHMARK_SIZE = 30  # Start small
BENCHMARK_SOURCE = "humaneval"  # Uses datasets library
```

Then run:
```bash
python main.py
```

## How It Works

### Baseline (Single-Shot)
1. Generate code once from task description
2. Run test suite
3. Record success/failure

### Verification (Retry Loop)
1. Generate code
2. Run test suite
3. If fails: extract error, feed back to LLM as feedback
4. LLM regenerates code from same prompt + error context
5. Repeat up to `MAX_RETRIES` times (default: 3)
6. Record success and # of attempts

### Output
Each experiment saves JSON with:
- Success rate (%)
- Detailed per-task results
- Generated code
- Test output/errors
- Attempt count

## Key Configuration

Edit `config.py` to customize:

```python
MODEL = "claude-haiku-4-5-20251001"  # Cheap for Day 1. Switch to sonnet for final.
TEMPERATURE = 0.7                     # Higher = more varied outputs
MAX_RETRIES = 3                       # Retry attempts
BENCHMARK_SIZE = 50                   # How many tasks to run
BENCHMARK_SOURCE = "mock"             # or "humaneval"
```

## Results

Look in `results/` directory after running. Each JSON has:

```json
{
  "experiment": "baseline",
  "success_rate": 0.45,
  "results": [
    {
      "task_id": "mock_0",
      "success": true,
      "attempts": 0,
      "code": "def add(a, b):\n    return a + b"
    },
    ...
  ]
}
```

## Next Steps (Day 2-3)

Once baseline works:

1. **Add static verification**: Run `pylint` / `mypy` on generated code
2. **Critic LLM pass**: Use a second LLM call to review generated diff
3. **Scale to 100+ tasks**: Real benchmark dataset
4. **Tune hyperparameters**: Max retries, temperature, prompt engineering

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Make sure `.env` exists and contains `ANTHROPIC_API_KEY=sk-...`

**"No module named 'pytest'"**
```bash
pip install pytest
```

**Subprocess timeout errors**
- Increase `TIMEOUT_SECONDS` in config.py
- Or reduce `BENCHMARK_SIZE` to ensure faster tests

**Python version too old**
- Requires Python 3.9+
- Check with `python --version`
- Upgrade via https://www.python.org or Anaconda Navigator

**API rate limits**
- Use `claude-haiku-4-5-20251001` for cheaper/faster testing
- Switch to `claude-sonnet-5` only for final run

## Estimated Time (Day 1)

- Environment setup: 30 min
- Install + first run: 20 min  
- Customization & debug: 1 hour
- Mock experiment run: 10-30 min (depends on retry loop overhead)
- **Total**: ~2-2.5 hours for working baseline

That leaves you 5-6 hours Day 1 to:
- Understand why certain tasks fail
- Experiment with different prompts
- Add static verification layer (lint/type check)
- Begin Day 2 tasks

---

**Goal for Day 1 Completion**: Have both baseline and verification experiments running, with quantified comparison results.
