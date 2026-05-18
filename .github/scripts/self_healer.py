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
TARGET_EXCEPTIONS = [ex.strip() for ex in exceptions_env.split(",") if ex.strip()]

def get_coding_standards():
    """Reads the coding standards, checking multiple likely paths."""
    potential_paths = [
        ".github/scripts/coding-standards.md",
        "coding-standards.md",
        "../coding-standards.md"
    ]

    for path in potential_paths:
        if os.path.exists(path):
            print(f"✅ Success: Loaded coding standards from {path}")
            with open(path, 'r') as file:
                return file.read()

    # --- DEBUGGING BLOCK ---
    print("❌ Warning: coding-standards.md not found in any expected location.")
    print("--- Debugging Info ---")
    print("Current Working Directory:", os.getcwd())

    scripts_dir = ".github/scripts/"
    if os.path.exists(scripts_dir):
        print(f"Contents of {scripts_dir}:", os.listdir(scripts_dir))
    else:
        print(f"Directory {scripts_dir} does not exist in the current working directory.")

    print("Contents of root directory:", os.listdir("."))
    print("----------------------")

    return "Apply general modern Java best practices."

def find_exception_in_reports():
    """Scans Maven surefire reports for any exception, prioritizing TARGET_EXCEPTIONS."""
    reports = glob.glob('target/surefire-reports/*.txt')

    fallback_content = None
    fallback_exc_type = None

    for report in reports:
        with open(report, 'r') as file:
            content = file.read()

            # 1. PRIORITY: Check for specific TARGET_EXCEPTIONS first
            for exc_type in TARGET_EXCEPTIONS:
                if exc_type in content:
                    print(f"🎯 Found prioritized target '{exc_type}' in report: {report}")
                    return content, exc_type

            # 2. FALLBACK: If we haven't found a prioritized one, look for ANY exception or error
            if not fallback_exc_type:
                # Regex looks for standard Java exception names (e.g., java.lang.RuntimeException, AssertionError)
                match = re.search(r'([a-zA-Z0-9_.]+(?:Exception|Error|Failure))', content)
                if match:
                    fallback_exc_type = match.group(1)
                    fallback_content = content
                    print(f"⚠️ Found non-targeted issue '{fallback_exc_type}' in report: {report}")
                elif "FAILURE!" in content or "ERROR!" in content:
                    # Absolute fallback if regex misses but maven says it failed
                    fallback_exc_type = "Generic Test Failure"
                    fallback_content = content
                    print(f"⚠️ Found generic test failure in report: {report}")

    # If we didn't find a target exception, but found SOMETHING, return the fallback
    if fallback_content and fallback_exc_type:
        return fallback_content, fallback_exc_type

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
        model="claude-sonnet-4-6", # Make sure this matches your Anthropic subscription
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
    print(f"Starting Self-Healing Analysis looking for prioritized targets: {TARGET_EXCEPTIONS}")

    standards = get_coding_standards()
    stack_trace, exc_type = find_exception_in_reports()

    if stack_trace and exc_type:
        print(f"Analysis complete. Analyzing cause: {exc_type}. Locating faulty file...")
        file_path = extract_failing_file_path(stack_trace)

        if file_path:
            print(f"Found faulty file: {file_path}. Generating fix...")
            fixed_code = generate_fix(file_path, stack_trace, exc_type, standards)

            print("Writing fix to file...\n\n", fixed_code)
            # with open(file_path, 'w') as file:
            #     file.write(fixed_code)
            #
            # print("Creating Pull Request...")
            # create_pull_request(file_path, exc_type)
        else:
            print("Could not map stack trace to a local file. Unable to proceed with auto-fix.")
    else:
        print("No exceptions or test failures detected in reports.")