from datasets import load_dataset
from verifier import BenchmarkTask
from typing import List
import random


class BenchmarkLoader:
    """Load code generation benchmarks (HumanEval, MBPP+)."""

    @staticmethod
    def load_humaneval_subset(num_tasks: int = 50, seed: int = 42) -> List[BenchmarkTask]:
        """Load HumanEval dataset with doctest format."""
        random.seed(seed)
        try:
            dataset = load_dataset("openai_humaneval")["test"]
        except:
            dataset = load_dataset("nuprl/HumanEvalPlus")["test"]

        tasks = []
        indices = random.sample(range(len(dataset)), min(num_tasks, len(dataset)))

        for idx in indices:
            item = dataset[idx]
            prompt = item.get("prompt", "")
            reference_code = item.get("canonical_solution", "")

            # Extract function name from prompt
            import re
            func_match = re.search(r"def (\w+)\(", prompt)
            func_name = func_match.group(1) if func_match else f"func_{idx}"

            # Create pytest-compatible test from docstring examples
            docstring = item.get("prompt", "")
            test_code = BenchmarkLoader._create_doctest_from_prompt(docstring, func_name)

            task = BenchmarkTask(
                task_id=f"humaneval_{idx}",
                prompt=prompt,
                reference_code=reference_code,
                test_code=test_code,
                difficulty="medium"
            )
            tasks.append(task)

        return tasks

    @staticmethod
    def _create_doctest_from_prompt(prompt: str, func_name: str) -> str:
        """Extract doctest examples from prompt and create pytest-compatible test."""
        import re

        # Extract doctest examples from the docstring
        # Look for lines like: >>> func_name(...) == result
        doctest_pattern = r'>>>.*?(?=\n(?:>>>|$))'
        matches = re.findall(doctest_pattern, prompt, re.DOTALL)

        if not matches:
            # Fallback: create a basic sanity check
            return f"""
def test_{func_name}():
    # Basic sanity test
    assert callable({func_name})
"""

        # Convert doctest to pytest format
        test_cases = []
        for match in matches:
            match = match.strip()
            if '>>>' in match:
                # Extract the code and expected result
                lines = match.split('\n')
                for line in lines:
                    if '>>>' in line:
                        # Extract code after >>>
                        code = line.replace('>>>', '').strip()
                        test_cases.append(code)

        if not test_cases:
            return f"""
def test_{func_name}():
    assert callable({func_name})
"""

        # Build pytest test
        test_code = f"""
def test_{func_name}():
"""
        for i, test_case in enumerate(test_cases[:5]):  # Limit to first 5 cases
            # Try to parse as assertion
            if '==' in test_case:
                test_code += f"    {test_case}\n"
            else:
                test_code += f"    {func_name}({test_case})  # sanity check\n"

        return test_code if test_code.count('\n') > 2 else f"""
def test_{func_name}():
    assert callable({func_name})
"""

    @staticmethod
    def load_mbpp_subset(num_tasks: int = 50, seed: int = 42) -> List[BenchmarkTask]:
        """Load MBPP+ dataset."""
        random.seed(seed)
        try:
            dataset = load_dataset("google-research-datasets/mbpp")["test"]
        except:
            dataset = load_dataset("mbpp")["test"]

        tasks = []
        indices = random.sample(range(len(dataset)), min(num_tasks, len(dataset)))

        for idx in indices:
            item = dataset[idx]
            # MBPP has different format
            task = BenchmarkTask(
                task_id=f"mbpp_{idx}",
                prompt=item.get("text", ""),
                reference_code=item.get("code", ""),
                test_code=item.get("test_list", [{}])[0],  # Take first test
                difficulty="medium"
            )
            tasks.append(task)

        return tasks

    @staticmethod
    def create_mock_tasks(num_tasks: int = 10) -> List[BenchmarkTask]:
        """Create mock tasks for quick testing (no internet needed)."""
        mock_prompts = [
            ("Write a function that returns the sum of two numbers.",
             "def add(a, b):\n    return a + b",
             'def test_add():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0'),
            ("Write a function that checks if a number is prime.",
             "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
             'def test_prime():\n    assert is_prime(2) == True\n    assert is_prime(17) == True\n    assert is_prime(4) == False'),
            ("Write a function that reverses a string.",
             "def reverse_string(s):\n    return s[::-1]",
             'def test_reverse():\n    assert reverse_string("hello") == "olleh"\n    assert reverse_string("") == ""'),
            ("Write a function that finds the maximum number in a list.",
             "def find_max(lst):\n    return max(lst)",
             'def test_max():\n    assert find_max([1, 5, 3, 9, 2]) == 9\n    assert find_max([-5, -1]) == -1'),
            ("Write a function that counts vowels in a string.",
             "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')",
             'def test_vowels():\n    assert count_vowels("hello") == 2\n    assert count_vowels("") == 0'),
            ("Write a function that checks if a string is a palindrome.",
             "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
             'def test_palindrome():\n    assert is_palindrome("racecar") == True\n    assert is_palindrome("hello") == False'),
            ("Write a function that returns the Fibonacci number at index n.",
             "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
             'def test_fib():\n    assert fibonacci(0) == 0\n    assert fibonacci(5) == 5'),
            ("Write a function that removes duplicates from a list.",
             "def remove_duplicates(lst):\n    return list(dict.fromkeys(lst))",
             'def test_remove_dups():\n    assert remove_duplicates([1, 2, 2, 3]) == [1, 2, 3]'),
            ("Write a function that flattens a nested list.",
             "def flatten(nested):\n    result = []\n    for item in nested:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result",
             'def test_flatten():\n    assert flatten([1, [2, [3, 4]], 5]) == [1, 2, 3, 4, 5]'),
            ("Write a function that sorts a list without using sort().",
             "def bubble_sort(lst):\n    n = len(lst)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if lst[j] > lst[j+1]:\n                lst[j], lst[j+1] = lst[j+1], lst[j]\n    return lst",
             'def test_sort():\n    assert bubble_sort([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]'),
        ]

        tasks = []
        for i in range(min(num_tasks, len(mock_prompts))):
            prompt, ref_code, test_code = mock_prompts[i]
            task = BenchmarkTask(
                task_id=f"mock_{i}",
                prompt=prompt,
                reference_code=ref_code,
                test_code=test_code,
                difficulty="easy"
            )
            tasks.append(task)

        return tasks
