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
# Setting a constant for the model to ensure valid API calls
CLAUDE_MODEL = "claude-sonnet-4-6"

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

    return "Apply general modern Java best practices."

def find_exception_in_reports():
    """Scans Maven surefire reports for any exception, prioritizing TARGET_EXCEPTIONS."""
    reports = glob.glob('target/surefire-reports/*.txt')

    fallback_content = None
    fallback_exc_type = None

    for report in reports:
        if not os.path.isfile(report):
            continue

        with open(report, 'r') as file:
            content = file.read()

            # Priority Check
            for exc_type in TARGET_EXCEPTIONS:
                if exc_type in content:
                    print(f"🎯 Found prioritized target '{exc_type}' in report: {report}")
                    return content, exc_type

            # Fallback Check
            if not fallback_exc_type:
                match = re.search(r'([a-zA-Z0-9_.]+(?:Exception|Error|Failure))', content)
                if match:
                    fallback_exc_type = match.group(1)
                    fallback_content = content
                    print(f"⚠️ Found non-targeted issue '{fallback_exc_type}' in report: {report}")

    if fallback_content and fallback_exc_type:
        return fallback_content, fallback_exc_type

    return None, None

def get_filename_from_ai(stack_trace):
    """STEP 1: Uses Claude to intelligently extract the faulty file name from a stack trace."""
    prompt = f"""
    Analyze the following Java stack trace. Identify the main project source file where the exception originated.
    Ignore standard Java libraries (e.g., java.base), testing frameworks (e.g., JUnit, Surefire), and Spring framework internal classes.
    
    Stack Trace:
    {stack_trace}
    
    Return EXACTLY AND ONLY the file name with its extension (e.g., NPETestService.java). Do not output any extra words, markdown, or punctuation.
    """

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}]
    )

    # Clean the output just in case the AI adds a period or space
    return message.content[0].text.strip().replace("`", "")

def extract_failing_file_path(stack_trace):
    """Finds the file path using AI instead of Regex."""
    print("\n--- AI-POWERED FILE EXTRACTION ---")

    # Ask AI for the file name
    file_name = get_filename_from_ai(stack_trace)
    print(f"🧠 AI identified the faulty file as: '{file_name}'")

    # Failsafe if AI returned something weird
    if not file_name.endswith(".java"):
        print(f"❌ AI returned an invalid file name: {file_name}")
        return None

    print(f"🔍 Searching repository for '{file_name}'...")

    # Search the local directory for the file the AI identified
    found_paths = []
    for root, dirs, files in os.walk('.'):
        if file_name in files:
            found_paths.append(os.path.join(root, file_name))

    if not found_paths:
        print(f"❌ SEARCH FAILED: '{file_name}' does not exist anywhere in the current directory.")
        return None

    selected_path = found_paths[0]
    print(f"✅ SEARCH SUCCESS: Found file at '{selected_path}'")
    print("----------------------------------\n")
    return selected_path

def generate_fix(file_path, stack_trace, exc_type, coding_standards):
    """STEP 2: Asks Claude to fix the exception in the code."""
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
        model=CLAUDE_MODEL,
        max_tokens=4000,
        system=system_instructions,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    fixed_code = message.content[0].text.replace('```java', '').replace('```', '').strip()
    return fixed_code

if __name__ == "__main__":
    print(f"Starting Self-Healing Analysis looking for prioritized targets: {TARGET_EXCEPTIONS}")

    standards = get_coding_standards()
    stack_trace, exc_type = find_exception_in_reports()

    if stack_trace and exc_type:
        print(f"Analysis complete. Analyzing cause: {exc_type}. Locating faulty file...")

        # This will now trigger the new AI extraction method
        print("stack trace: ", stack_trace)
        file_path = extract_failing_file_path(stack_trace)

        if file_path:
            print(f"Found faulty file: {file_path}. Generating fix...")
            fixed_code = generate_fix(file_path, stack_trace, exc_type, standards)

            print("Writing fix to file...\n\n", fixed_code)

            # Uncomment below when you are ready to write to disk and PR
            # with open(file_path, 'w') as file:
            #     file.write(fixed_code)
            #
            # print("Creating Pull Request...")
            # create_pull_request(file_path, exc_type)
        else:
            print("Could not map stack trace to a local file. Unable to proceed with auto-fix.")
    else:
        print("No exceptions or test failures detected in reports.")