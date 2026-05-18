import os
import glob
import subprocess
import re
import anthropic

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

# def create_pull_request(file_path, exc_type):
#     """Creates a git branch, commits the fix, and raises a PR."""
#     short_exc_name = exc_type.split('.')[-1]
#     branch_name = f"ai-fix-{short_exc_name.lower()}"
#
#     subprocess.run(["git", "config", "--global", "user.name", "AI Self-Healer (Claude)"])
#     subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
#
#     subprocess.run(["git", "checkout", "-B", branch_name])
#     subprocess.run(["git", "add", file_path])
#     subprocess.run(["git", "commit", "-m", f"🤖 AI Auto-Fix: Resolved {short_exc_name}"])
#     subprocess.run(["git", "push", "-f", "origin", branch_name])
#
#     os.environ["GH_TOKEN"] = os.environ.get("GITHUB_TOKEN")
#     subprocess.run([
#         "gh", "pr", "create",
#         "--title", f"🤖 AI Auto-Fix: {short_exc_name}",
#         "--body", f"This PR was generated automatically by Claude to fix a `{exc_type}` detected during the CI pipeline.\n\n**Note:** Claude was instructed to follow the rules defined in `coding-standards.md`.",
#         "--base", "master",
#         "--head", branch_name
#     ])
#     print("Pull Request created successfully!")

if __name__ == "__main__":
    print(f"Starting Self-Healing Analysis looking for: {TARGET_EXCEPTIONS}")

    # Read the standards first
    standards = get_coding_standards("coding-standards.md")

    stack_trace, exc_type = find_exception_in_reports()

    if stack_trace and exc_type:
        print(f"{exc_type} detected. Locating faulty file...")
        file_path = extract_failing_file_path(stack_trace)

        if file_path:
            print(f"Found faulty file: {file_path}. Generating fix...")
            # Pass the standards to the AI generator
            fixed_code = generate_fix(file_path, stack_trace, exc_type, standards)

            print("Writing fix to file...", fixed_code)
            # with open(file_path, 'w') as file:
            #     file.write(fixed_code)
            #
            # print("Creating Pull Request...")
            # create_pull_request(file_path, exc_type)
        else:
            print("Could not map stack trace to a local file.")
    else:
        print("No target exceptions detected in test reports.")