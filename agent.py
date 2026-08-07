from anthropic import Anthropic
from verifier import CodeVerifier, BenchmarkTask
import json
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CodeGenerationAgent:
    """Agent that generates code with self-verification loop."""

    def __init__(self, model: str, api_key: str, temperature: float = 0.7):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.verifier = CodeVerifier()

    def generate_code_single_shot(self, task: BenchmarkTask) -> str:
        """Single-shot code generation (baseline)."""
        func_name_instruction = ""
        if task.expected_function_name:
            func_name_instruction = f"\nIMPORTANT: The function MUST be named '{task.expected_function_name}' (not any variation)."

        prompt = f"""You are an expert Python programmer. Solve the following problem:

{task.prompt}{func_name_instruction}

CRITICAL REQUIREMENTS:
1. Provide ONLY the Python function/class implementation, no explanations
2. Do NOT use any external APIs or imports for the actual computation
3. Write simple, self-contained code that solves the problem directly
4. Do NOT add any main() block or test code
5. The implementation must be minimal and focused ONLY on the core logic
6. The function name MUST exactly match what the tests expect

Example of GOOD format:
def example_function(x):
    return x + 1

Example of BAD format:
def example_func(x):  # WRONG - name doesn't match
    return x + 1

Now solve the problem. Provide only the function definition."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        code = response.content[0].text
        # Clean up markdown code blocks if present
        if code.strip().startswith("```"):
            code = code.strip()
            code = code.replace("```python\n", "").replace("```\n", "").replace("```", "")
        logger.debug(f"Generated code for {task.task_id}:\n{code[:200]}...")
        return code

    def generate_code_with_retry(
        self,
        task: BenchmarkTask,
        max_retries: int = 3
    ) -> Tuple[str, bool, int, str]:
        """Code generation with verify-retry loop.

        Returns:
            (generated_code, success, retry_count, details)
        """
        generated_code = self.generate_code_single_shot(task)
        details = []

        for attempt in range(max_retries):
            success, output, error = self.verifier.verify_code(
                generated_code,
                task.test_code,
                task.task_id
            )

            if success:
                details.append(f"✓ PASSED on attempt {attempt + 1}")
                return generated_code, True, attempt, '\n'.join(details)

            # Extract error and retry
            error_context = self.verifier.extract_error_context(error or output)
            details.append(f"✗ Attempt {attempt + 1} failed\nError: {error_context[:200]}")

            if attempt < max_retries - 1:
                # Retry with error feedback
                func_name_instruction = ""
                if task.expected_function_name:
                    func_name_instruction = f"\nCRITICAL: The function name MUST be '{task.expected_function_name}' - if you see a NameError about this, fix it!"

                retry_prompt = f"""The previous code failed tests with this error:

{error_context}

Original problem:
{task.prompt}{func_name_instruction}

Previous code:
```python
{generated_code}
```

CRITICAL REQUIREMENTS FOR FIX:
1. Do NOT use external APIs, libraries, or client calls
2. Keep the code simple and self-contained
3. Focus ONLY on fixing the logic error shown above
4. Do NOT add extra code like main() or test cases
5. If there's a NameError about function name, change the function name to match what the test expects
6. The function MUST be named exactly: {task.expected_function_name}

Fix the code to pass the tests. Provide ONLY the corrected function/class implementation."""

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=self.temperature,
                    messages=[
                        {"role": "user", "content": retry_prompt}
                    ]
                )
                generated_code = response.content[0].text
                # Clean up markdown code blocks
                if generated_code.strip().startswith("```"):
                    generated_code = generated_code.strip()
                    generated_code = generated_code.replace("```python\n", "").replace("```\n", "").replace("```", "")

        return generated_code, False, max_retries - 1, '\n'.join(details)

    def run_experiment(
        self,
        task: BenchmarkTask,
        use_verification: bool = True
    ) -> dict:
        """Run single experiment on a task.

        Returns:
            Result dict with success, attempts, code, and details.
        """
        if use_verification:
            code, success, attempts, details = self.generate_code_with_retry(task)
        else:
            code = self.generate_code_single_shot(task)
            success, output, error = self.verifier.verify_code(
                code,
                task.test_code,
                task.task_id
            )
            attempts = 0
            details = output if success else error

        return {
            "task_id": task.task_id,
            "success": success,
            "attempts": attempts,
            "code": code,
            "details": details
        }
