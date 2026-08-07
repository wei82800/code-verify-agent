# Quick Start - 5 Minutes to First Run

## Step 1: Setup Environment (2 min)

```bash
# Navigate to project directory
cd C:\Users\USER\Desktop\code-verify-agent

# Create .env file
copy .env.example .env

# Edit .env and add your API key (use any text editor)
# ANTHROPIC_API_KEY=sk-...
```

## Step 2: Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

## Step 3: Verify Setup (30 sec)

```bash
python test_setup.py
```

Should show all ✓ checks. If not, fix the issues it reports.

## Step 4: Run First Experiment (30 sec - 5 min depending on retries)

```bash
python main.py
```

Watch it run! You'll see:
- Task by task progress
- Baseline results
- Verification results
- Side-by-side comparison

## Expected Output

```
INFO:__main__:Running BASELINE experiment (single-shot, no verification)...
INFO:__main__:[1/10] Task mock_0
INFO:__main__:  ✓ PASSED
...
Baseline Results: 7/10 (70.0%)

INFO:__main__:Running VERIFICATION experiment (with retry loop)...
INFO:__main__:[1/10] Task mock_0
INFO:__main__:  ✓ PASSED (attempts: 1)
...
Verification Results: 9/10 (90.0%)
Average attempts: 1.22

============================================================
ABLATION STUDY SUMMARY
============================================================
Baseline (no verification):        7/10 (70.0%)
With verification loop:            9/10 (90.0%)
Improvement:                       +20.0%
Tasks improved by verification:    2/3
============================================================
```

## Step 5: Check Results

Look in `results/` folder for JSON files with detailed output.

---

**That's it!** You now have a working code generation agent with self-verification loop.

Next: Read [DAY1_CHECKLIST.md](DAY1_CHECKLIST.md) for what to do with these results and how to expand.
