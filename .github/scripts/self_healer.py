import os
import glob
import subprocess
import re
import json
import anthropic
from pathlib import Path
from git_manager import GitManager
from typing import List, Dict, Optional
import logging

# 1. Initialize the Anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY environment variable is not set.")
    exit(1)

client = anthropic.Anthropic(api_key=api_key)
CLAUDE_MODEL = "claude-sonnet-4-6"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def load_skills(file_path=".github/scripts/ai-skills.json"):
    """Loads the AI skills (exceptions and framework rules) from an external JSON file."""
    if os.path.exists(file_path):
        logger.info(f"Loaded AI skills from {file_path}")
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        logger.warning(f"{file_path} not found. Proceeding with empty skills.")
        return {"target_exceptions": [], "spring_di_rules": []}

def get_coding_standards(file_path=".github/scripts/coding-standards.md"):
    """Reads the coding standards from an external markdown file."""
    if os.path.exists(file_path):
        logger.info(f"Loaded coding standards from {file_path}")
        with open(file_path, 'r') as file:
            return file.read()
    else:
        logger.warning(f"{file_path} not found. Proceeding with default AI knowledge.")
        return "Apply general modern Java best practices."

def find_exception_in_reports(target_exceptions):
    """Scans Maven surefire reports for target exceptions loaded from the skills file."""
    reports = glob.glob('target/surefire-reports/*.txt')

    fallback_content, fallback_exc_type = None, None

    for report in reports:
        if not os.path.isfile(report): continue
        with open(report, 'r') as file:
            content = file.read()
            # Prioritized check
            for exc_type in target_exceptions:
                if exc_type in content:
                    logger.info(f"Found targeted {exc_type} in report: {report}")
                    return content, exc_type

            # Fallback if no target exception is found but a failure occurred
            if not fallback_exc_type:
                match = re.search(r'([a-zA-Z0-9_.]+(?:Exception|Error|Failure))', content)
                if match:
                    fallback_exc_type = match.group(1)
                    fallback_content = content

    return fallback_content, fallback_exc_type

def get_failing_files_from_ai(stack_trace: str, skills: dict) -> List[str]:
    """Uses Claude to intelligently identify ALL failing files from the stack trace."""

    spring_rules = "\n".join([f"- {rule}" for rule in skills.get("spring_di_rules", [])])

    prompt = f"""
    Analyze the following Java stack trace to identify the main project source files that need to be modified.
    
    Rules for identification:
    1. Standard Errors: Look for the highest user-created classes in the execution stack.
    2. Spring Dependency Injection Errors: The user code will NOT be in the execution stack. Read the exception message carefully to identify missing annotations or bean conflicts.
    
    Specific Spring Context:
    {spring_rules}
    
    3. Ignore standard Java libraries (java.base) and framework internal classes.
    
    Stack Trace:
    {stack_trace}
    
    Return ONLY a raw JSON list of exact file names with their extensions (e.g., ["NPETestServiceImpl.java", "MyConfig.java"]). Do not output markdown blocks or any other text.
    """

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        # Clean the output and parse JSON
        raw_output = message.content[0].text.strip().replace("```json", "").replace("```", "")
        file_names = json.loads(raw_output)

        # Now find where these files live in the local directory
        found_paths = []
        for file_name in file_names:
            for root, dirs, files in os.walk('.'):
                if file_name in files:
                    found_paths.append(os.path.join(root, file_name))
                    break # Stop searching once found

        return found_paths
    except json.JSONDecodeError:
        logger.error(f"Failed to parse AI file identification response: {message.content[0].text}")
        return []

def generate_fix(file_path, stack_trace, exc_type, coding_standards, skills):
    """Asks Claude to fix the exception using external coding standards and skill rules."""
    with open(file_path, 'r') as file:
        java_code = file.read()

    spring_rules = "\n".join([f"- {rule}" for rule in skills.get("spring_di_rules", [])])

    system_instructions = f"""
    You are a Senior Java Staff Engineer resolving CI/CD pipeline failures. 
    You must strictly adhere to the following Team Coding Standards.
    
    ### TEAM CODING STANDARDS ###
    {coding_standards}
    
    ### KNOWN FRAMEWORK PATTERNS ###
    {spring_rules}
    """

    user_prompt = f"""
    The following code throws a {exc_type}.
    
    Stack Trace:
    {stack_trace}
    
    Java Code (File: {file_path}):
    {java_code}
    
    Fix the {exc_type} in the code addressing the root cause indicated by the stack trace.
    Return ONLY the raw, updated Java code. Do not include markdown formatting like ```java.
    """

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        system=system_instructions,
        messages=[{"role": "user", "content": user_prompt}]
    )

    return message.content[0].text.replace('```java', '').replace('```', '').strip()

def create_pr_and_commit(git_manager: GitManager, fixes_applied: List[Dict]) -> Optional[str]:
    """Create feature branch, commit fixes, push branch, and open GitHub Pull Request."""
    try:
        if not fixes_applied:
            return None

        branch_name = git_manager.create_branch()
        logger.info(f"Created branch: {branch_name}")

        fixed_files = [fix["file"] for fix in fixes_applied if "file" in fix]

        if not git_manager.commit_changes(files=fixed_files):
            logger.warning("Commit failed.")
            return None

        git_manager.push_branch(branch_name)
        pr_url = git_manager.create_pr(branch_name=branch_name, files_changed=fixed_files)
        logger.info(f"Created PR: {pr_url}")
        return pr_url
    except Exception as e:
        logger.error(f"PR creation workflow failed: {str(e)}")
        return None

if __name__ == "__main__":
    workspace = Path(os.getcwd())
    git_manager = GitManager(workspace)
    fixes_applied = []

    # Load Skills and Standards
    skills = load_skills(".github/scripts/ai-skills.json")
    standards = get_coding_standards(".github/scripts/coding-standards.md")

    stack_trace, exc_type = find_exception_in_reports(skills.get("target_exceptions", []))

    if stack_trace and exc_type:
        logger.info(f"Analyzing cause: {exc_type}")

        # Extracted to return a list of files rather than just one
        failing_files = get_failing_files_from_ai(stack_trace, skills)

        if failing_files:
            logger.info(f"AI identified failing files: {failing_files}. Generating fixes...")

            # Iterate through all files identified by the AI and apply fixes
            for file_path in failing_files:
                fixed_code = generate_fix(file_path, stack_trace, exc_type, standards, skills)
                with open(file_path, "w") as file:
                    file.write(fixed_code)

                fixes_applied.append({"file": file_path, "exception": exc_type})

            # Validate all fixes at once
            logger.info("Running Maven test to validate fixes...")
            test_result = subprocess.run(["mvn", "test"], capture_output=True, text=True)

            if test_result.returncode == 0:
                logger.info("Tests passed! Generating Pull Request...")
                pr_url = create_pr_and_commit(git_manager, fixes_applied)
                if pr_url:
                    print(f"PR Created: {pr_url}")
                else:
                    print("Failed to create PR.")
            else:
                logger.error("Fix validation failed. Tests still not passing.")
                # print(test_result.stdout)
        else:
            logger.warning("Could not map stack trace to local files. Unable to proceed with auto-fix.")
    else:
        logger.info("No target exceptions or test failures detected in reports.")