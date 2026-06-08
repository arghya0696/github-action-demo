def get_failing_files_from_ai(stack_trace: str, skills: dict) -> List[str]:
    dynamic_knowledge_base = build_dynamic_context(skills)
    model_version = skills["model_version"]

    # --- HARDCODED PRODUCT DEFAULT ---
    default_prompt = """Analyze the following error log to identify the main project source files that need to be modified.

CRITICAL EXTRACTION CONSTRAINTS:
1. Identify ONLY the deepest file in the stack trace that belongs to our application (the root cause). Do not return every file in the trace.
2. DO NOT return Test classes unless the error is strictly a compilation syntax error within the test itself.

{dynamic_knowledge_base}

Stack Trace / Error Log:
{stack_trace}"""

    raw_prompt = parse_prompt_config(skills.get("file_extraction_prompt"), default_prompt)

    prompt = raw_prompt.format(
        dynamic_knowledge_base=dynamic_knowledge_base,
        stack_trace=stack_trace
    )

    # HARDCODED XML EXTRACTION REQUIREMENT
    prompt += "\n\nCRITICAL FORMATTING REQUIREMENT:\nYou MUST NOT output any explanations, reasoning, or conversational text. Return ONLY the XML block.\nReturn the output wrapped EXACTLY in <files> tags containing only the JSON array. Example:\n<files>\n[\"path/to/broken_file.ext\"]\n</files>"

    message = client.messages.create(
        model=model_version,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_output = message.content[0].text.strip()
    logger.info(f"AI Raw Extraction Output:\n{raw_output}")

    match = re.search(r'<files>\s*(.*?)\s*</files>', raw_output, re.DOTALL)

    try:
        if match:
            json_str = match.group(1).replace("```json", "").replace("```", "").strip()
            file_names = json.loads(json_str)
        else:
            clean_str = re.sub(r'^.*?(\[.*\]).*$', r'\1', raw_output, flags=re.DOTALL)
            file_names = json.loads(clean_str)

        found_paths = []
        for file_name in file_names:
            if os.path.isfile(file_name):
                found_paths.append(file_name)
                continue

            basename = os.path.basename(file_name)
            found = False
            for root, dirs, files in os.walk('.'):
                if basename in files:
                    found_paths.append(os.path.join(root, basename))
                    found = True
                    break

            if not found:
                logger.warning(f"AI suggested '{file_name}', but it does not exist in the repository.")

        return found_paths
    except json.JSONDecodeError:
        logger.error(f"Failed to parse AI file identification response.")
        return []

def generate_fix(file_path, stack_trace, exc_type, coding_standards, skills):
    with open(file_path, 'r') as file:
        code_content = file.read()

    dynamic_knowledge_base = build_dynamic_context(skills)
    model_version = skills["model_version"]

    # --- HARDCODED PRODUCT DEFAULT ---
    default_sys = """You are a Senior Software Engineer resolving CI/CD pipeline failures.
You must strictly adhere to the following Team Coding Standards.

CRITICAL CONSTRAINTS:
1. NEVER delete, skip, or comment out test cases to resolve a failure.
2. NEVER alter the class name, class definition, or package declaration of the provided file.
3. NEVER delete unrelated existing methods. Only fix the specific method causing the error.
4. DO NOT completely rewrite the file. Keep the structure intact.

### TEAM CODING STANDARDS ###
{coding_standards}

{dynamic_knowledge_base}"""

    raw_sys_prompt = parse_prompt_config(skills.get("fix_generation_system_prompt"), default_sys)

    system_instructions = raw_sys_prompt.format(
        coding_standards=coding_standards,
        dynamic_knowledge_base=dynamic_knowledge_base
    )

    # --- HARDCODED PRODUCT DEFAULT ---
    default_user = """The following code throws a {exc_type}.

Error Log / Stack Trace:
{stack_trace}

Code (File: {file_path}):
{code}

Fix the {exc_type} in the code addressing the root cause indicated by the stack trace or compiler error."""

    raw_user_prompt = parse_prompt_config(skills.get("fix_generation_user_prompt"), default_user)

    user_prompt = raw_user_prompt.format(
        exc_type=exc_type,
        stack_trace=stack_trace,
        file_path=file_path,
        code=code_content
    )

    # HARDCODED XML EXTRACTION REQUIREMENT (Language Agnostic)
    user_prompt += "\n\nCRITICAL FORMATTING REQUIREMENT:\nReturn the updated code wrapped EXACTLY in <code> tags. NO markdown. NO preamble.\nExample:\n<code>\n// your updated code here...\n</code>"

    message = client.messages.create(
        model=model_version,
        max_tokens=4000,
        system=system_instructions,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw_output = message.content[0].text

    match = re.search(r'<code>\s*(.*?)\s*</code>', raw_output, re.DOTALL)

    if match:
        fixed_code = match.group(1).strip()
    else:
        fixed_code = re.sub(r'^```[a-zA-Z]*\n', '', raw_output)
        fixed_code = fixed_code.replace('```', '').strip()

    return fixed_code