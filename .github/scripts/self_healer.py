import os
import glob
import subprocess
import re
import anthropic

# 1. Initialize the Anthropic client
# We extract the API key from the environment variables configured by GitHub Actions.
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY environment variable is not set.")
    exit(1)

client = anthropic.Anthropic(api_key=api_key)

def find_npe_in_reports():
    """Scans Maven surefire reports for NullPointerExceptions and extracts the failing class."""
    reports = glob.glob('target/surefire-reports/*.txt')
    for report in reports:
        with open(report, 'r') as file:
            content = file.read()
            if 'java.lang.NullPointerException' in content:
                print(f"Found NPE in report: {report}")
                return content
    return None

def extract_failing_file_path(stack_trace):
    """A basic heuristic to find the first project file in the stack trace."""
    match = re.search(r'at ([\w\.]+)\(([\w]+\.java):(\d+)\)', stack_trace)
    if match:
        class_path = match.group(1).replace('.', '/')
        file_name = match.group(2)

        # Search the repo for this file
        for root, dirs, files in os.walk('.'):
            if file_name in files:
                return os.path.join(root, file_name)
    return None

def generate_fix(file_path, stack_trace):
    """Asks Claude to fix the NPE in the provided file."""
    with open(file_path, 'r') as file:
        java_code = file.read()

    prompt = f"""
    You are an expert Java developer. The following code throws a NullPointerException.
    
    Stack Trace:
    {stack_trace}
    
    Java Code:
    {java_code}
    
    Fix the NullPointerException by adding appropriate null checks or Optional wrapping. 
    Return ONLY the raw, updated Java code. Do not include markdown formatting like ```java.
    """

    # 2. Make the API call to Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022", # Best balance of speed and coding ability
        max_tokens=4000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # 3. Extract the response text
    fixed_code = message.content[0].text.replace('```java', '').replace('```', '').strip()
    return fixed_code

# def create_pull_request(file_path):
#     """Creates a git branch, commits the fix, and raises a PR via GitHub CLI."""
#     branch_name = "ai-fix-npe-auto-claude"
#
#     # Git commands
#     subprocess.run(["git", "config", "--global", "user.name", "AI Self-Healer (Claude)"])
#     subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
#     subprocess.run(["git", "checkout", "-b", branch_name])
#     subprocess.run(["git", "add", file_path])
#     subprocess.run(["git", "commit", "-m", "🤖 AI Auto-Fix: Resolved NullPointerException"])
#     subprocess.run(["git", "push", "origin", branch_name])
#
#     # GitHub CLI command to create PR
#     os.environ["GH_TOKEN"] = os.environ.get("GITHUB_TOKEN")
#     subprocess.run([
#         "gh", "pr", "create",
#         "--title", "🤖 AI Auto-Fix: NullPointerException",
#         "--body", "This PR was generated automatically by Claude to fix a NullPointerException detected during the CI pipeline. **Please review the logic before merging.**",
#         "--base", "master",
#         "--head", branch_name
#     ])
#     print("Pull Request created successfully!")

if __name__ == "__main__":
    print("Starting Self-Healing Analysis with Claude...")
    stack_trace = find_npe_in_reports()

    if stack_trace:
        print("NPE detected. Locating faulty file...")
        file_path = extract_failing_file_path(stack_trace)

        if file_path:
            print(f"Found faulty file: {file_path}. Generating fix...")
            fixed_code = generate_fix(file_path, stack_trace)

            print("Writing fix to file...", fixed_code)
            # with open(file_path, 'w') as file:
            #     file.write(fixed_code)
            #
            # print("Creating Pull Request...")
            # create_pull_request(file_path)
        else:
            print("Could not map stack trace to a local file.")
    else:
        print("No NPE detected in test reports.")