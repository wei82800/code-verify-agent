from __future__ import annotations

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional
import json


class CodeVerifier:
    """Execute and verify generated code in isolated environment."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    def verify_code(
        self,
        generated_code: str,
        test_code: str,
        task_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Execute generated code against test suite.

        Returns:
            (success: bool, output: str, error: Optional[str])
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write generated code
            code_file = Path(tmpdir) / "solution.py"
            code_file.write_text(generated_code, encoding='utf-8')

            # Create test file with import statement
            test_with_import = f"from solution import *\n\n{test_code}"
            test_file = Path(tmpdir) / "test_solution.py"
            test_file.write_text(test_with_import, encoding='utf-8')

            try:
                # Run tests with proper Python path
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-v", "--tb=line"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env={**dict(subprocess.os.environ), "PYTHONPATH": tmpdir}
                )

                success = result.returncode == 0
                output = result.stdout + "\n" + result.stderr
                error = None if success else result.stderr or result.stdout

                return success, output, error

            except subprocess.TimeoutExpired:
                return False, "", f"Timeout after {self.timeout_seconds}s"
            except Exception as e:
                return False, "", f"Execution error: {str(e)}"

    def extract_error_context(self, error_output: str) -> str:
        """Extract key error information from test output."""
        lines = error_output.split('\n')
        # Keep last N lines with most relevant error info
        relevant = [l for l in lines if l.strip() and any(
            x in l.lower() for x in ['error', 'assert', 'failed', 'exception', 'traceback']
        )]
        return '\n'.join(relevant[-10:]) if relevant else error_output[-500:]


class BenchmarkTask:
    """Represent a single benchmark task."""

    def __init__(self, task_id: str, prompt: str, reference_code: str, test_code: str, difficulty: str = "medium"):
        self.task_id = task_id
        self.prompt = prompt
        self.reference_code = reference_code
        self.test_code = test_code
        self.difficulty = difficulty
        self.expected_function_name = self._extract_function_name()

    def _extract_function_name(self) -> str:
        """Extract the expected function name from test code."""
        import re
        # Look for patterns like "def test_xxx():" and extract xxx
        # Then infer the function name from common patterns
        match = re.search(r'def test_(\w+)\(', self.test_code)
        if match:
            test_func_name = match.group(1)
            # Common mappings
            mapping = {
                "add": "add",
                "prime": "is_prime",
                "reverse": "reverse_string",
                "max": "find_max",
                "vowels": "count_vowels",
                "palindrome": "is_palindrome",
                "fib": "fibonacci",
                "remove_dups": "remove_duplicates",
                "flatten": "flatten",
                "sort": "bubble_sort",
            }
            return mapping.get(test_func_name, test_func_name)
        return ""

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "difficulty": self.difficulty
        }
