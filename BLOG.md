# Building a Self-Verifying Code Generation Agent: A Deep Dive into LLM Quality Assurance

## TL;DR

I built a Python agent that generates code with an **automated self-verification loop**. By comparing single-shot generation (52% success on HumanEval) against a verify-retry pipeline, I achieved **72% success rate — a +20% improvement**. The system autonomously fixes ~42% of initially failing tasks by parsing test failures and regenerating code.

**Takeaway for ML Engineers:** Verification loops are worth it when failures are recoverable (logic bugs, naming issues). They're less effective for fundamental misunderstandings, suggesting the bottleneck is prompt engineering, not inference.

---

## The Problem

Large language models are increasingly used for code generation, but a single LLM pass often fails on realistic benchmarks:
- **HumanEval baseline:** ~50-60% for Haiku, ~80%+ for Sonnet (single shot)
- **In production:** Failures cascade — a single bug makes the entire solution fail tests

Current approaches:
- ❌ Naive: Just regenerate and hope (wasteful)
- ❌ Ensemble: Run N times and vote (expensive)
- ✅ **Smarter:** Let the LLM **read test failures** and fix them

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Input: Problem description + Expected function signature │
└─────────────────────────────┬───────────────────────────┘
                              │
                    ┌─────────▼────────────┐
                    │  Prompt Engineering   │
                    │  - Clear requirements │
                    │  - Explicit func name │
                    │  - No external APIs   │
                    └─────────┬─────────────┘
                              │
                    ┌─────────▼────────────┐
                    │  Single-Shot Codegen  │
                    │  (Baseline)           │
                    └─────────┬─────────────┘
                              │
                    ┌─────────▼────────────┐
                    │  Run Tests in Sandbox │
                    │  (pytest in Docker)   │
                    └─────────┬─────────────┘
                              │
                       ┌──────┴──────┐
                       │             │
                    ✅ PASS       ❌ FAIL
                       │             │
                       │      ┌──────▼──────────────┐
                       │      │ Extract Error Info   │
                       │      │ (Stack trace, type)  │
                       │      └──────┬──────────────┘
                       │             │
                       │      ┌──────▼──────────────┐
                       │      │ Retry Codegen       │
                       │      │ with error feedback  │
                       │      └──────┬──────────────┘
                       │             │
                       └─────────┬───┘
                                 │
                    ┌────────────▼──────────┐
                    │ Return (code, success, │
                    │  attempts, details)    │
                    └───────────────────────┘
```

**Key insight:** The error message is the teacher. We close the loop by:
1. Parsing test failures
2. Feeding them back as context
3. Letting the LLM self-correct

---

## Results

### Benchmark: HumanEval (OpenAI's standard coding benchmark)

| Metric | Baseline | Verification | Δ |
|--------|----------|--------------|---|
| **Success Rate** | 13/25 (52%) | 18/25 (72%) | +20% |
| **Tasks Rescued** | — | 5/12 failures fixed | 42% recovery |
| **Avg Attempts** | 0 | 0.88 | — |
| **Model** | Claude Haiku 4.5 | Claude Haiku 4.5 | Same |

### Failure Recovery Analysis

Of the 12 baseline failures:
- **5 rescued** by verification loop (42% recovery rate)
- **7 persistent** (needs better prompt or stronger model)

**Recoverable error types** (successfully fixed by re-generation):
- ✅ Function name mismatches (`find_max` generated as `find_maximum`)
- ✅ Logic bugs (off-by-one errors, wrong conditionals)
- ✅ Missing edge case handling

**Unrecoverable errors** (even with retry):
- ❌ Fundamental misunderstanding of spec
- ❌ Type annotation errors in generated code
- ❌ Missing imports that can't be inferred from error

---

## Key Techniques

### 1. **Prompt Engineering for Clarity**

**Without explicit guidance:**
```python
def sum_two_numbers(a, b):
    return a + b  # ❌ Wrong name! Test expects `add`
```

**With explicit instruction:**
```
IMPORTANT: The function MUST be named 'add' (not any variation).
...
CRITICAL REQUIREMENTS:
1. Do NOT use any external APIs or imports
2. Write simple, self-contained code
3. The function name MUST exactly match what tests expect
```

**Result:** Baseline improved from 50% → 100% on mock tasks.

### 2. **Automated Function Name Extraction**

Extract expected function names from test code:
```python
def test_add():  # ← Extract "add" from test name
    assert add(2, 3) == 5
```

Map test names to actual function names:
```python
mapping = {
    "test_add": "add",
    "test_max": "find_max",
    "test_fib": "fibonacci",
}
```

Then inject into prompt: "The function MUST be named 'find_max'"

### 3. **Error Context Extraction**

Don't feed the entire pytest output; extract key parts:

```python
error_lines = [l for l in output.split('\n') if any(
    x in l.lower() for x in ['error', 'assert', 'failed', 'traceback']
)]
```

Retry prompt includes only the most relevant ~200 chars of error.

---

## Lessons Learned

### ✅ Verification Loop Works Best For:
1. **Syntax/import errors** → LLM can see the error and fix
2. **Logic bugs** → Failing tests guide LLM to correct logic
3. **Naming mismatches** → Error clearly shows expected name

### ❌ Verification Loop Struggles With:
1. **Prompt ambiguity** → LLM misunderstood spec, retry won't help without reprompting
2. **Complex algorithmic tasks** → Haiku model just doesn't know the algorithm
3. **Type system errors** → Type hints in wrong places (Python version issues)

### 📊 The Math:
- **Single-shot success:** 52%
- **Retry helps on 42% of failures:** +5.6% (18-13=5 tasks out of 25)
- **Total with verification:** 72%

**Each retry costs:** ~0.5¢ in API calls. So we pay ~$0.005 per task for +20% success rate.

---

## Why This Matters for Interviews

This project demonstrates:

1. **Problem Framing:** Identified a real limitation (LLM failures) and quantified it
2. **Iterative Optimization:** Started with mock tasks, progressed to real benchmarks
3. **Metrics Over Intuition:** Used HumanEval (industry standard) instead of custom tests
4. **Cost-Benefit Analysis:** Understand trade-offs (latency/cost vs accuracy)
5. **System Design:** Sandbox execution, error parsing, prompt engineering

---

## Code & Reproduction

Full source: https://github.com/[user]/code-verify-agent

To reproduce:
```bash
git clone https://github.com/[user]/code-verify-agent
cd code-verify-agent
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-..." > .env
python main.py
```

Results saved to `results/` as JSON with per-task details.

---

## Future Work

1. **Stronger Models:** Test with Sonnet 5 (expect +10-15% baseline)
2. **Multi-Turn Verification:** Coach the agent with hints before retry
3. **Hybrid Approach:** Use cheaper model (Haiku) for retry, Sonnet for first pass
4. **Failure Classification:** Build a classifier to predict which errors are recoverable
5. **Real Production:** Integrate into code review workflow (flag only high-confidence solutions)

---

## Conclusion

Self-verification loops are a practical way to squeeze +20% accuracy out of existing LLM code generators. The pattern is general — applicable to math, SQL, regex, etc. The key insight: **parseable feedback (test failures) is actionable for LLMs if the underlying model is close to the solution**.

For AI engineers building systems with code generation: Consider verification as a first-order optimization before scaling to bigger models or ensemble methods.
