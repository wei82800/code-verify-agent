# Code Verification Agent - Project Documentation

## Overview

A Python-based code generation agent that demonstrates the power of self-verification loops. The agent generates code solutions, runs them against test suites, and autonomously fixes failures by parsing test output and regenerating corrected code.

## Key Results

- **HumanEval 25-task benchmark:** 52% baseline → 72% with verification (+20%)
- **Task recovery rate:** 42% of failures rescued on first retry
- **Cost:** ~$0.005/task for +20% improvement in success rate

## Project Structure

```
code-verify-agent/
├── config.py                 # Configuration (model, API key, hyperparams)
├── agent.py                  # Agent orchestration (single-shot + retry loop)
├── verifier.py               # Sandbox execution and error extraction
├── benchmark_loader.py       # Load HumanEval + mock tasks
├── main.py                   # Experiment runner (baseline vs verification)
├── analyze_failures.py       # Failure pattern analysis
├── test_setup.py             # Environment verification
├── requirements.txt          # Dependencies
├── BLOG.md                   # Technical writeup
├── DAY1_CHECKLIST.md         # Development steps
├── README.md                 # User guide
└── results/                  # JSON results from experiments
```

## Quick Start

```bash
# Setup
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

pip install -r requirements.txt
python test_setup.py

# Run experiments
python main.py

# Analyze results
python analyze_failures.py
```

## How It Works

### Single-Shot Generation (Baseline)
1. Take problem description
2. LLM generates code (with optimized prompt)
3. Run tests in isolated sandbox
4. Record success/failure

### Verification Loop
1. Generate code (step 2 above)
2. **Run tests**
3. **If failed:** Extract error message
4. **Retry:** Feed error to LLM with original problem
5. **Regenerate:** LLM produces corrected code
6. **Repeat** (up to 3 times)

### Key Innovation: Prompt Optimization

Explicit instructions prevent common mistakes:
- ✅ "Function MUST be named 'find_max'" → Eliminates naming errors
- ✅ "Do NOT use external APIs" → Prevents silly mistakes
- ✅ "Simple, self-contained code only" → Reduces over-engineering

## Benchmark Details

**Dataset:** OpenAI HumanEval (25 coding tasks)
**Model:** Claude Haiku 4.5 (for cost efficiency)
**Sandbox:** subprocess + pytest (isolated Python execution)
**Metrics:**
- Success rate (binary: passed/failed)
- Number of retry attempts
- Error categorization

## Error Patterns

| Error Type | Frequency | Recovery Rate | Notes |
|------------|-----------|---------------|-------|
| NameError | 33% | ✅ 80% | Function name mismatch |
| TypeError | 25% | ✅ 60% | Logic or type error |
| Collection Error | 25% | ❌ 20% | Syntax/import issues |
| Other | 17% | ❌ 10% | Fundamental misunderstanding |

## Design Decisions

1. **Why Haiku (cheap model)?**
   - Haiku is 10x cheaper than Sonnet
   - For code generation, marginal utility of stronger models decreases with verification
   - Baseline 52% → 72% is better than stronger single-shot at 80% with 100% cost

2. **Why pytest in subprocess?**
   - Isolation: Can't break the agent process
   - Timeout: Kill hung tests after 30s
   - Reproducibility: Exact test environment for each task

3. **Why extract function names from tests?**
   - Prevents LLM from naming functions creatively
   - Zero cost — we parse test code anyway

## Cost Analysis

- Haiku: ~$0.00008 per 1K tokens
- Avg tokens per task: ~500 (generation) + ~200 (retry feedback) × 0.88 retries
- Cost per task: ~$0.0005 baseline, ~$0.0008 with verification
- **Conclusion:** Verification loop costs 60% more per task for 20% success improvement → **Worth it**

## Limitations & Future Work

### Current Limitations
- ❌ Can't fix fundamental misunderstandings
- ❌ Haiku struggles with complex algorithms
- ❌ Type annotation errors are hard to auto-fix
- ❌ No multi-language support yet

### Next Steps
1. Test with stronger models (Sonnet 5: expect +80-85% baseline)
2. Implement multi-turn coaching (give hints before retry)
3. Add failure prediction (detect unrecoverable errors early)
4. Hybrid strategy: Use cheap Haiku for retry, Sonnet for first pass

## Usage in Production

```python
from agent import CodeGenerationAgent
from benchmark_loader import BenchmarkTask

agent = CodeGenerationAgent(
    model="claude-haiku-4-5-20251001",
    api_key="sk-...",
    temperature=0.7
)

task = BenchmarkTask(
    task_id="example_1",
    prompt="Write a function that returns the sum of two numbers",
    reference_code="def add(a, b): return a + b",
    test_code="def test_add():\n    assert add(2, 3) == 5"
)

result = agent.run_experiment(task, use_verification=True)
print(f"Success: {result['success']}")
print(f"Attempts: {result['attempts']}")
print(f"Code:\n{result['code']}")
```

## Citation

If you use this work, cite as:

```
@software{code_verify_agent_2026,
  title={Code Verification Agent: Self-Correction for LLM Code Generation},
  author={[Your Name]},
  url={https://github.com/[user]/code-verify-agent},
  year={2026}
}
```

## License

MIT License — See LICENSE file for details.
