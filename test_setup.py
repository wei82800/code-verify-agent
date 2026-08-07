#!/usr/bin/env python3
"""Quick setup verification script."""

import sys
import subprocess
from pathlib import Path


def check_package(package_name):
    """Check if a package is installed."""
    try:
        __import__(package_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} (install with: pip install {package_name})")
        return False


def check_env_file():
    """Check if .env file exists and has API key."""
    env_file = Path(".env")
    if not env_file.exists():
        print("✗ .env file not found (copy from .env.example and add API key)")
        return False

    with open(env_file) as f:
        content = f.read()
        if "ANTHROPIC_API_KEY" in content and "sk-" in content:
            print("✓ .env file with API key")
            return True
        else:
            print("✗ .env file missing ANTHROPIC_API_KEY or invalid format")
            return False


def main():
    print("Checking setup...\n")

    all_ok = True

    # Check Python version
    if sys.version_info >= (3, 9):
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"✗ Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.9+)")
        all_ok = False

    # Check packages
    print("\nPackages:")
    all_ok &= check_package("anthropic")
    all_ok &= check_package("datasets")
    all_ok &= check_package("pytest")
    all_ok &= check_package("dotenv")

    # Check .env
    print("\nConfiguration:")
    all_ok &= check_env_file()

    print("\n" + "="*50)
    if all_ok:
        print("✓ All checks passed! Ready to run: python main.py")
    else:
        print("✗ Fix issues above, then run: python test_setup.py again")
    print("="*50)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
