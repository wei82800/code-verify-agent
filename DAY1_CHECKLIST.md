# Day 1 Checklist - Code Verification Agent

## Phase 1: Setup (30 min)

- [ ] Copy `.env.example` to `.env`
- [ ] Add your `ANTHROPIC_API_KEY` to `.env`
- [ ] Run `pip install -r requirements.txt`
- [ ] Run `python test_setup.py` and verify all checks pass

## Phase 2: First Run (20 min)

- [ ] Run `python main.py` with default config (uses 10 mock tasks)
- [ ] Watch both experiments complete (should take 2-5 min)
- [ ] Verify output folder `results/` contains two JSON files
- [ ] Check the console output for:
  - Baseline success rate
  - Verification success rate  
  - Improvement percentage

## Phase 3: Understand Results (30 min)

- [ ] Open one of the JSON result files and understand the structure
- [ ] Pick 2-3 tasks where verification helped (baseline failed, verification succeeded)
- [ ] Read the generated code and understand WHY the retry loop fixed it
- [ ] Pick 1 task where even verification failed, understand the error

**Questions to answer for yourself:**
- What's the baseline success rate? (expect 40-70% on mock tasks)
- How much does verification improve it? (expect 10-30% boost)
- What types of errors does the agent fix vs. can't fix?

## Phase 4: First Customization (1-2 hours)

Choose ONE of the following to deepen understanding:

### Option A: Experiment with Prompts
- [ ] Edit the prompt in `agent.py`'s `generate_code_single_shot()` method
- [ ] Try different prompt styles:
  - Add "use efficient algorithms"
  - Add "follow PEP8 style"
  - Add "add docstrings"
- [ ] Re-run and compare results
- [ ] Document which prompt style performed best

### Option B: Add Static Verification Layer
- [ ] Create `static_verifier.py` with basic checks:
  - Run `pylint` on generated code
  - Check code length (avoid too-long functions)
  - Simple AST checks (e.g., no infinite loops)
- [ ] Integrate into `verifier.py` 
- [ ] Run experiment again and measure impact

### Option C: Scale to Real Benchmark
- [ ] Edit `config.py`: set `BENCHMARK_SOURCE = "humaneval"` and `BENCHMARK_SIZE = 30`
- [ ] First install datasets: `pip install datasets`
- [ ] Run main.py again
- [ ] Compare results on real tasks vs. mock
- [ ] Document any new failure patterns

### Option D: Analyze Failure Cases
- [ ] Write a script `analyze_failures.py` that:
  - Loads the JSON results
  - Extracts all failed tasks
  - Groups failures by error type (syntax error, logic error, timeout, etc.)
  - Shows success rate by error category
- [ ] Run it on the verification results
- [ ] Document top failure reasons

## Phase 5: Documentation (30 min)

- [ ] Create `DAY1_RESULTS.md` with:
  - Baseline vs Verification results summary
  - Key findings (what helped, what didn't)
  - Any changes you made to the code/prompts
  - Screenshots or tables of results
  - Next steps for Day 2

## Success Criteria for Day 1

✓ Both baseline and verification experiments run without errors  
✓ You have quantified results showing improvement from verification loop  
✓ You understand why verification helps in concrete examples  
✓ You've attempted at least one customization (prompt, static checks, or real benchmark)  
✓ You have a README-friendly summary of results  

## Time Budget

- Phase 1: 30 min
- Phase 2: 20 min
- Phase 3: 30 min
- Phase 4: 2-3 hours
- Phase 5: 30 min
- **Buffer**: 1-2 hours for debugging/exploration

**Total**: 5-6 hours, leaving room for Day 2 starts

## Troubleshooting Help

| Issue | Solution |
|-------|----------|
| "No module named anthropic" | `pip install anthropic` |
| ".env file not found" | Run `cp .env.example .env` then edit it |
| API key errors | Make sure your API key in .env starts with "sk-" |
| Tests hang or timeout | Increase `TIMEOUT_SECONDS` in config.py or reduce `BENCHMARK_SIZE` |
| Out of memory | Use smaller `BENCHMARK_SIZE` (e.g., 10 instead of 50) |
| Want cheaper testing | Set `MODEL = "claude-haiku-4-5-20251001"` in config.py |

---

Once Day 1 is done, you'll have a working scaffold that clearly demonstrates:
1. The value of verification loops in code generation
2. Quantified metrics to back up your claims
3. A professional-looking pipeline ready to extend

This is very suitable for a portfolio/interview story: "I built an agent that demonstrates 30% improvement through self-verification, with rigorous A/B testing."
