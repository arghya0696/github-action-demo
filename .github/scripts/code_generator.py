#!/usr/bin/env python3
"""
Code Generator Module

Integrates with Anthropic Claude API to:
- Analyze errors
- Generate fixes
- Provide explanations
- Include confidence scoring

Optimized for minimal API usage with caching and batching.
"""

import os
import json
import logging
import time
from typing import Dict, Optional, List
from functools import lru_cache

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic library not installed")
    print("Install with: pip install anthropic")
    raise

logger = logging.getLogger(__name__)


class APIConfig:
    """API configuration and optimization settings."""
    
    MODELS = {
        "lite": "claude-3-5-haiku-20241022",      # Fastest, cheapest (~$0.80/M input)
        "standard": "claude-3-5-sonnet-20241022",  # Balanced (~$3/M input)
        "premium": "claude-3-opus-20250729"        # Most capable (~$15/M input)
    }
    
    TEMPERATURE_BY_TIER = {
        "lite": 0.1,        # Lower = more deterministic
        "standard": 0.3,    # Balanced
        "premium": 0.2      # Careful generation
    }
    
    MAX_TOKENS_BY_TIER = {
        "lite": 1024,
        "standard": 2048,
        "premium": 4096
    }


class CodeGenerator:
    """Generates code fixes using Claude API."""
    
    def __init__(self, api_tier: str = "standard"):
        """Initialize code generator."""
        self.api_tier = api_tier
        self.model = APIConfig.MODELS.get(api_tier, APIConfig.MODELS["standard"])
        self.temperature = APIConfig.TEMPERATURE_BY_TIER[api_tier]
        self.max_tokens = APIConfig.MAX_TOKENS_BY_TIER[api_tier]
        
        # Initialize Claude client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.call_count = 0
        self.tokens_used = 0
        
        logger.info(f"CodeGenerator initialized with tier: {api_tier}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Max tokens: {self.max_tokens}")
    
    def analyze_errors(self, prompt: str, error_batch) -> Optional[Dict]:
        """
        Send batch of errors to Claude for analysis.
        
        Returns:
            Dict with root_cause, fixes, confidence, and test_recommendations
        """
        try:
            logger.info(f"Calling Claude API ({self.api_tier})...")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Make API call with retry logic
            response = self._call_claude_with_retry(prompt)
            
            if not response:
                logger.error("Claude API call failed")
                return None
            
            # Parse response
            analysis = self._parse_response(response)
            
            if analysis:
                # Log API usage
                self.call_count += 1
                self.tokens_used += response.usage.input_tokens + response.usage.output_tokens
                
                logger.info(f"Claude analysis completed")
                logger.info(f"Tokens used: {response.usage.input_tokens + response.usage.output_tokens}")
                logger.info(f"Total calls: {self.call_count}")
                
                return analysis
            else:
                logger.error("Failed to parse Claude response")
                return None
        
        except anthropic.APIConnectionError as e:
            logger.error(f"API connection error: {str(e)}")
            return None
        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            return None
        except anthropic.APIStatusError as e:
            logger.error(f"API error: {e.status_code} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Claude analysis: {str(e)}", exc_info=True)
            return None
    
    def _call_claude_with_retry(self, prompt: str, max_retries: int = 3) -> Optional:
        """Call Claude API with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                logger.debug(f"API call succeeded on attempt {attempt + 1}")
                return response
            
            except anthropic.RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            
            except anthropic.APIConnectionError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Connection error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def _parse_response(self, response) -> Optional[Dict]:
        """Parse Claude response and extract structured data."""
        try:
            # Extract text from response
            content = response.content[0].text if response.content else ""
            
            if not content:
                logger.warning("Empty response content from Claude")
                return None
            
            # Parse JSON from response
            # Claude may include markdown formatting, so extract JSON
            json_match = None
            
            # Try direct JSON parsing first
            try:
                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                pass
            
            # Try to extract JSON from markdown code blocks
            import re
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            json_match = re.search(json_pattern, content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                analysis = json.loads(json_str)
                return analysis
            
            # Try to find JSON object in response
            json_pattern = r'\{[\s\S]*\}'
            json_match = re.search(json_pattern, content)
            
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
                return analysis
            
            logger.warning(f"Could not parse response as JSON. Content: {content[:200]}")
            return None
        
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            logger.debug(f"Response content: {content}")
            return None
    
    def generate_fix_with_explanation(
        self, 
        error_type: str, 
        stack_trace: str, 
        source_code: str,
        file_path: str
    ) -> Optional[Dict]:
        """
        Generate a fix with detailed explanation for a single error.
        Use this for interactive/premium analysis.
        """
        prompt = f"""You are an expert Java developer. Analyze and fix the following error:

ERROR TYPE: {error_type}
FILE: {file_path}

SOURCE CODE:
```java
{source_code}
```

STACK TRACE:
{stack_trace}

Provide:
1. Root cause analysis (2-3 sentences)
2. Fixed Java code (complete, compilable)
3. Confidence level (0-100)
4. Why this fix works
5. Potential side effects to consider

Return ONLY valid JSON:
{{
  "root_cause": "explanation",
  "fixed_code": "complete java code",
  "confidence": 85,
  "explanation": "why this works",
  "side_effects": ["possible side effect 1"]
}}"""
        
        response = self._call_claude_with_retry(prompt)
        if response:
            return self._parse_response(response)
        return None
    
    def analyze_test_failure(
        self,
        test_class: str,
        test_method: str,
        assertion_error: str,
        source_code: str
    ) -> Optional[Dict]:
        """Analyze test failures and suggest fixes."""
        prompt = f"""Analyze this failing unit test and suggest a fix:

TEST CLASS: {test_class}
TEST METHOD: {test_method}

ASSERTION ERROR:
{assertion_error}

SOURCE CODE BEING TESTED:
```java
{source_code}
```

Provide:
1. What the test expects vs what it's actually getting
2. Root cause in the source code
3. Fixed source code (not test code)
4. Confidence (0-100)

Return JSON:
{{
  "test_analysis": "what's wrong",
  "root_cause": "in the actual code",
  "fixed_code": "fixed source code",
  "confidence": 80
}}"""
        
        response = self._call_claude_with_retry(prompt)
        if response:
            return self._parse_response(response)
        return None
    
    def suggest_refactoring(
        self,
        class_name: str,
        code: str,
        issues: List[str]
    ) -> Optional[Dict]:
        """Suggest refactoring to fix code quality issues."""
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        
        prompt = f"""Refactor this Java class to address the following issues:

CLASS: {class_name}

ISSUES:
{issues_text}

CURRENT CODE:
```java
{code}
```

Provide refactored code that:
1. Addresses all issues
2. Maintains the same functionality
3. Follows Java best practices
4. Includes proper null checks

Return JSON:
{{
  "refactored_code": "complete refactored class",
  "changes_made": ["change 1", "change 2"],
  "confidence": 85
}}"""
        
        response = self._call_claude_with_retry(prompt)
        if response:
            return self._parse_response(response)
        return None


class PromptOptimizer:
    """Optimizes prompts to reduce token usage."""
    
    @staticmethod
    def summarize_error(error_context) -> str:
        """Create concise error summary."""
        return f"""
ERROR: {error_context.error_type}
FILE: {error_context.file_path}:{error_context.line_number}
MESSAGE: {error_context.error_message}
CONTEXT:
{error_context.source_context}
"""
    
    @staticmethod
    def batch_errors_prompt(error_batch) -> str:
        """Create efficient prompt for multiple errors."""
        errors_summary = []
        for i, error in enumerate(error_batch.errors, 1):
            errors_summary.append(
                f"Error {i}: {error.error_type} in {error.file_path}:{error.line_number}"
            )
        
        return "\n".join(errors_summary)
    
    @staticmethod
    def reduce_context(source_code: str, max_lines: int = 50) -> str:
        """Reduce source code context while preserving meaning."""
        lines = source_code.split('\n')
        if len(lines) <= max_lines:
            return source_code
        
        # Keep imports and method signature
        condensed = []
        for line in lines:
            if 'import' in line or 'public ' in line or 'private' in line:
                condensed.append(line)
        
        # Add first 30 lines
        condensed.extend(lines[:30])
        
        return '\n'.join(condensed[:max_lines])


class ResponseCache:
    """Simple cache for Claude responses (in-memory for a single run)."""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, prompt_hash: str) -> Optional[Dict]:
        """Get cached response."""
        return self.cache.get(prompt_hash)
    
    def set(self, prompt_hash: str, response: Dict):
        """Cache response."""
        self.cache[prompt_hash] = response
    
    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Create hash of prompt."""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()
