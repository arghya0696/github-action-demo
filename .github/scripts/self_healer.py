import os
import glob
import subprocess
import re
import anthropic
from git_manager import GitManager
from typing import List, Dict, Optional
from datetime import datetime
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)
# 1. Initialize the Anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY environment variable is not set.")
    exit(1)

client = anthropic.Anthropic(api_key=api_key)

# 2. Fetch target exceptions from the environment
exceptions_env = os.environ.get("TARGET_EXCEPTIONS", "java.lang.NullPointerException")
TARGET_EXCEPTIONS = [ex.strip() for ex in exceptions_env.split(",")]

def get_coding_standards(file_path=".github/scripts/coding-standards.md"):
    """Reads the coding standards from an external markdown file."""
    if os.path.exists(file_path):
        print(f"Loaded coding standards from {file_path}")
        with open(file_path, 'r') as file:
            return file.read()
    else:
        print(f"Warning: {file_path} not found. Proceeding with default AI knowledge.")
        return "Apply general modern Java best practices."

def find_exception_in_reports():
    """Scans Maven surefire reports for target exceptions."""
    reports = glob.glob('target/surefire-reports/*.txt')
    for report in reports:
        with open(report, 'r') as file:
            content = file.read()
            for exc_type in TARGET_EXCEPTIONS:
                if exc_type in content:
                    print(f"Found {exc_type} in report: {report}")
                    return content, exc_type
    return None, None

def extract_failing_file_path(stack_trace):
    """Finds the first project file in the stack trace."""
    match = re.search(r'at ([\w\.]+)\(([\w]+\.java):(\d+)\)', stack_trace)
    if match:
        class_path = match.group(1).replace('.', '/')
        file_name = match.group(2)

        for root, dirs, files in os.walk('.'):
            if file_name in files:
                return os.path.join(root, file_name)
    return None

def generate_fix(file_path, stack_trace, exc_type, coding_standards):
    """Asks Claude to fix the exception using external coding standards."""
    with open(file_path, 'r') as file:
        java_code = file.read()

    # Inject the external standards into the System Prompt
    system_instructions = f"""
    You are a Senior Java Staff Engineer resolving CI/CD pipeline failures. 
    You must strictly adhere to the following Team Coding Standards when writing fixes.
    If you violate these standards, your Pull Request will be rejected.
    
    ### TEAM CODING STANDARDS ###
    {coding_standards}
    """

    user_prompt = f"""
    The following code throws a {exc_type}.
    
    Stack Trace:
    {stack_trace}
    
    Java Code:
    {java_code}
    
    Fix the {exc_type} in the code addressing the root cause indicated by the stack trace.
    Return ONLY the raw, updated Java code. Do not include markdown formatting like ```java.
    """

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_instructions,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    fixed_code = message.content[0].text.replace('```java', '').replace('```', '').strip()
    return fixed_code

def _run_command(command: List[str], cwd: str = ".") -> str:
    """
    Execute shell command safely and return stdout.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(e.stderr)

        raise RuntimeError(
            f"Git command failed: {' '.join(command)}"
        ) from e


def create_pr_and_commit(fixes_applied: List[Dict]) -> Optional[str]:
    """
    Commit AI-generated fixes and create GitHub PR.
    """

    if not fixes_applied:
        logger.warning("No fixes to commit.")
        return None

    try:
        # Configure git identity
        git_user = os.getenv("GIT_USER_NAME", "github-actions[bot]")
        git_email = os.getenv(
            "GIT_USER_EMAIL",
            "41898282+github-actions[bot]@users.noreply.github.com"
        )

        _run_command(["git", "config", "user.name", git_user])
        _run_command(["git", "config", "user.email", git_email])

        # Create branch
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        branch_name = f"autoheal/{timestamp}"

        logger.info(f"Creating branch: {branch_name}")

        _run_command(["git", "checkout", "-b", branch_name])

        # Stage files
        fixed_files = []

        for fix in fixes_applied:
            file_path = fix.get("file")

            if file_path and os.path.exists(file_path):
                fixed_files.append(file_path)

        if not fixed_files:
            logger.warning("No files available to commit.")
            return None

        _run_command(["git", "add"] + fixed_files)

        # Validate staged changes
        staged = _run_command(
            ["git", "diff", "--cached", "--name-only"]
        )

        if not staged.strip():
            logger.warning("No staged changes detected.")
            return None

        exceptions = sorted(
            list({
                fix.get("exception", "UnknownException")
                for fix in fixes_applied
            })
        )

        commit_message = (
            f"fix(ci): automated remediation for "
            f"{', '.join(exceptions)}"
        )

        logger.info("Creating commit...")

        _run_command([
            "git",
            "commit",
            "-m",
            commit_message
        ])

        logger.info("Pushing branch...")

        _run_command([
            "git",
            "push",
            "--set-upstream",
            "origin",
            branch_name
        ])

        logger.info("Creating PR...")

        pr_body = f"""
## Automated Self-Healing Fix

### Fixed Exceptions
{chr(10).join(f"- {e}" for e in exceptions)}

### Modified Files
{chr(10).join(f"- {f}" for f in fixed_files)}

Generated automatically by AI remediation pipeline.
"""

        pr_url = _run_command([
            "gh",
            "pr",
            "create",
            "--title",
            commit_message,
            "--body",
            pr_body,
            "--base",
            "main",
            "--head",
            branch_name
        ])

        logger.info(f"PR Created: {pr_url}")

        return pr_url

    except Exception as e:
        logger.error(str(e))
        logger.error(traceback.format_exc())

        return None

if __name__ == "__main__":

    print(f"Starting Self-Healing Analysis for: {TARGET_EXCEPTIONS}")

    fixes_applied = []

    # Load coding standards
    standards = get_coding_standards(
        ".github/scripts/coding-standards.md"
    )

    # Detect failing exception
    stack_trace, exc_type = find_exception_in_reports()

    if stack_trace and exc_type:

        print(f"{exc_type} detected.")

        file_path = extract_failing_file_path(stack_trace)

        if file_path:

            print(f"Faulty file located: {file_path}")

            fixed_code = generate_fix(
                file_path,
                stack_trace,
                exc_type,
                standards
            )

            # Backup original file
            backup_path = f"{file_path}.bak"

            with open(file_path, "r") as original:
                original_content = original.read()

            with open(backup_path, "w") as backup:
                backup.write(original_content)

            # Write fixed code
            with open(file_path, "w") as updated:
                updated.write(fixed_code)

            print(f"Applied fix to: {file_path}")

            # Run Maven tests
            print("Running Maven verification...")

            test_result = subprocess.run(
                ["mvn", "test"],
                capture_output=True,
                text=True
            )

            if test_result.returncode == 0:

                print("Tests passed successfully.")

                fixes_applied.append({
                    "file": file_path,
                    "exception": exc_type
                })

                pr_url = create_pr_and_commit(fixes_applied)

                if pr_url:
                    print(f"Pull Request created: {pr_url}")
                else:
                    print("Failed to create Pull Request.")

            else:

                print("Tests failed after remediation.")
                print(test_result.stdout)
                print(test_result.stderr)

                # Restore backup
                with open(file_path, "w") as restore:
                    restore.write(original_content)

                print("Original file restored.")

        else:
            print("Could not map stack trace to source file.")

    else:
        print("No target exceptions found.")