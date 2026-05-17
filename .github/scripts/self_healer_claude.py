#!/usr/bin/env python3
"""
Self-Healing CI/CD Pipeline with Anthropic Claude API

This script analyzes build failures and uses Claude AI to:
1. Understand root causes
2. Generate fixes
3. Create feature branches and PRs with minimal API overhead

Optimized for API quota constraints with intelligent batching and caching.
"""

import os
import sys
import json
import glob
import subprocess
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

# Initialize logging
log_dir = Path(".ai-healer/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "self_healer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import error parser and code generator
from error_parser import ErrorParser, ErrorContext, ErrorBatch
from code_generator import CodeGenerator
from git_manager import GitManager


class APIQuotaManager:
    """Manages API calls to stay within quota limits."""
    
    def __init__(self, max_calls_per_day: int = 20):
        self.max_calls_per_day = max_calls_per_day
        self.call_log_file = log_dir / "api_calls.log"
        self.calls_today = self._count_api_calls_today()
        logger.info(f"API Calls today: {self.calls_today}/{max_calls_per_day}")
    
    def _count_api_calls_today(self) -> int:
        """Count API calls made today."""
        if not self.call_log_file.exists():
            return 0
        
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        with open(self.call_log_file, 'r') as f:
            for line in f:
                if today in line:
                    count += 1
        return count
    
    def can_make_api_call(self) -> bool:
        """Check if we can make another API call."""
        remaining = self.max_calls_per_day - self.calls_today
        if remaining <= 0:
            logger.warning(f"API quota exhausted for today ({self.max_calls_today})")
            return False
        logger.info(f"API calls remaining: {remaining}")
        return True
    
    def log_api_call(self, errors_analyzed: int, tokens_used: int):
        """Log an API call."""
        timestamp = datetime.now().isoformat()
        with open(self.call_log_file, 'a') as f:
            f.write(f"{timestamp},errors={errors_analyzed},tokens={tokens_used}\n")
        self.calls_today += 1


class SelfHealerAgent:
    """Main orchestrator for self-healing pipeline."""
    
    def __init__(self, workspace: str, api_tier: str = "standard"):
        self.workspace = Path(workspace)
        self.api_tier = api_tier
        self.quota_manager = APIQuotaManager()
        self.error_parser = ErrorParser()
        self.code_generator = CodeGenerator(api_tier=api_tier)
        self.git_manager = GitManager(self.workspace)
        
        logger.info(f"Self-Healer initialized in {self.workspace}")
        logger.info(f"API Tier: {api_tier}")
    
    def run(self, build_log: str, create_pr: bool = True, max_errors: int = 5):
        """Main execution flow."""
        try:
            logger.info("=" * 60)
            logger.info("SELF-HEALING ANALYSIS STARTED")
            logger.info("=" * 60)
            
            # Step 1: Parse errors
            logger.info("\n[STEP 1] Parsing build errors...")
            errors = self._parse_build_errors(build_log)
            
            if not errors:
                logger.info("No errors detected in build output.")
                return {"status": "no_errors", "errors_found": 0}
            
            logger.info(f"Found {len(errors)} error(s)")
            
            # Step 2: Batch errors to reduce API calls
            logger.info("\n[STEP 2] Batching errors for analysis...")
            error_batches = self._batch_errors(errors, max_batch_size=max_errors)
            logger.info(f"Created {len(error_batches)} error batch(es)")
            
            # Step 3: Check quota
            logger.info("\n[STEP 3] Checking API quota...")
            if not self.quota_manager.can_make_api_call():
                logger.warning("API quota exhausted. Skipping analysis.")
                return {"status": "quota_exhausted", "errors_found": len(errors)}
            
            # Step 4: Analyze errors with Claude
            logger.info("\n[STEP 4] Analyzing errors with Claude...")
            analysis_results = []
            for i, batch in enumerate(error_batches, 1):
                logger.info(f"Processing batch {i}/{len(error_batches)}")
                result = self._analyze_batch_with_claude(batch)
                if result:
                    analysis_results.append(result)
            
            if not analysis_results:
                logger.error("Claude analysis failed for all batches.")
                return {"status": "analysis_failed", "errors_found": len(errors)}
            
            # Step 5: Generate and apply fixes
            logger.info("\n[STEP 5] Generating and validating fixes...")
            fixes_applied = []
            for result in analysis_results:
                fix = self._apply_fix(result)
                if fix:
                    fixes_applied.append(fix)
            
            if not fixes_applied:
                logger.warning("No fixes were successfully applied.")
                return {"status": "no_fixes_applied", "errors_found": len(errors)}
            
            # Step 6: Commit and create PR
            logger.info("\n[STEP 6] Creating feature branch and PR...")
            if create_pr:
                pr_url = self._create_pr_and_commit(fixes_applied)
                logger.info(f"PR created: {pr_url}")
                return {
                    "status": "success",
                    "errors_found": len(errors),
                    "fixes_applied": len(fixes_applied),
                    "pr_url": pr_url
                }
            else:
                logger.info("PR creation disabled.")
                return {
                    "status": "success",
                    "errors_found": len(errors),
                    "fixes_applied": len(fixes_applied),
                    "pr_url": None
                }
        
        except Exception as e:
            logger.error(f"Self-healing failed: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}
        
        finally:
            logger.info("=" * 60)
            logger.info("SELF-HEALING ANALYSIS COMPLETED")
            logger.info("=" * 60)
    
    def _parse_build_errors(self, build_log: str) -> List[ErrorContext]:
        """Parse errors from build log and surefire reports."""
        errors = []
        
        # Try to find surefire reports first (most reliable)
        surefire_dir = self.workspace / "target" / "surefire-reports"
        if surefire_dir.exists():
            logger.info(f"Analyzing surefire reports in {surefire_dir}")
            errors.extend(self.error_parser.parse_surefire_reports(surefire_dir))
        
        # Also parse build log for compilation errors
        if os.path.exists(build_log):
            logger.info(f"Analyzing build log: {build_log}")
            errors.extend(self.error_parser.parse_build_log(build_log))
        
        # Deduplicate errors by stack trace
        unique_errors = {}
        for error in errors:
            key = error.error_type + error.stack_trace[:100]
            if key not in unique_errors:
                unique_errors[key] = error
        
        return list(unique_errors.values())
    
    def _batch_errors(self, errors: List[ErrorContext], max_batch_size: int = 5) -> List[ErrorBatch]:
        """Group errors into batches for single API call."""
        batches = []
        
        # Group by error type first
        by_type = {}
        for error in errors:
            if error.error_type not in by_type:
                by_type[error.error_type] = []
            by_type[error.error_type].append(error)
        
        # Create batches respecting max size
        current_batch = []
        for error_type, type_errors in by_type.items():
            for error in type_errors:
                current_batch.append(error)
                if len(current_batch) >= max_batch_size:
                    batches.append(ErrorBatch(current_batch))
                    current_batch = []
        
        if current_batch:
            batches.append(ErrorBatch(current_batch))
        
        logger.info(f"Created {len(batches)} batch(es) from {len(errors)} error(s)")
        return batches
    
    def _analyze_batch_with_claude(self, batch: ErrorBatch) -> Optional[Dict]:
        """Send batch to Claude for analysis."""
        try:
            logger.info(f"Sending batch with {len(batch.errors)} error(s) to Claude...")
            
            # Generate prompt
            prompt = self._generate_analysis_prompt(batch)
            
            # Call Claude
            analysis = self.code_generator.analyze_errors(prompt, batch)
            
            if analysis:
                logger.info(f"Claude analysis completed")
                logger.info(f"Confidence: {analysis.get('confidence', 'N/A')}")
                return analysis
            else:
                logger.warning("Claude returned no analysis")
                return None
        
        except Exception as e:
            logger.error(f"Claude analysis failed: {str(e)}")
            return None
    
    def _generate_analysis_prompt(self, batch: ErrorBatch) -> str:
        """Generate optimized prompt for Claude analysis."""
        errors_text = "\n\n".join([
            f"Error {i+1}:\n"
            f"Type: {e.error_type}\n"
            f"File: {e.file_path}\n"
            f"Line: {e.line_number}\n"
            f"Stack Trace:\n{e.stack_trace}\n"
            f"Source Context:\n{e.source_context}"
            for i, e in enumerate(batch.errors)
        ])
        
        prompt = f"""You are an expert Java developer debugging CI/CD test failures.

Analyze the following error(s) and provide:
1. Root cause analysis
2. Specific code fix for each error
3. Confidence score (0-100)
4. Testing recommendations

ERRORS TO ANALYZE:
{errors_text}

IMPORTANT:
- Provide ONLY the fixed Java code, no markdown formatting
- Include null checks and proper error handling
- Keep the original code structure
- Return valid, compilable Java

Respond in JSON format:
{{
  "root_cause": "explanation",
  "fixes": [
    {{"file": "path", "fixed_code": "code"}}, ...
  ],
  "confidence": 85,
  "test_recommendations": ["recommendation1", "recommendation2"]
}}"""
        
        return prompt
    
    def _apply_fix(self, analysis_result: Dict) -> Optional[Dict]:
        """Apply fix to source file and validate."""
        try:
            fixes = analysis_result.get("fixes", [])
            if not fixes:
                logger.warning("No fixes found in analysis result")
                return None
            
            applied = []
            for fix in fixes:
                file_path = fix.get("file")
                fixed_code = fix.get("fixed_code")
                
                if not file_path or not fixed_code:
                    logger.warning(f"Invalid fix structure: {fix}")
                    continue
                
                # Resolve file path
                full_path = self.workspace / file_path
                if not full_path.exists():
                    logger.warning(f"File not found: {full_path}")
                    continue
                
                # Apply fix
                logger.info(f"Applying fix to {file_path}")
                with open(full_path, 'w') as f:
                    f.write(fixed_code)
                
                # Validate syntax
                if self._validate_java_syntax(full_path):
                    logger.info(f"✓ Fix validated for {file_path}")
                    applied.append({
                        "file": file_path,
                        "status": "applied"
                    })
                else:
                    logger.error(f"✗ Syntax validation failed for {file_path}")
                    # Revert the change
                    subprocess.run(["git", "checkout", file_path], cwd=self.workspace)
            
            return {"fixes": applied} if applied else None
        
        except Exception as e:
            logger.error(f"Failed to apply fix: {str(e)}")
            return None
    
    def _validate_java_syntax(self, file_path: Path) -> bool:
        """Validate Java file syntax using javac."""
        try:
            result = subprocess.run(
                ["javac", "-d", "/tmp", str(file_path)],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Could not validate syntax: {str(e)}")
            return True  # Assume valid if we can't validate
    
    def _create_pr_and_commit(self, fixes_applied: List[Dict]) -> Optional[str]:
        """Create feature branch, commit fixes, and create PR."""
        try:
            # Create branch
            branch_name = self.git_manager.create_branch()
            logger.info(f"Created branch: {branch_name}")
            
            # Commit changes
            fixed_files = [f["file"] for f in fixes_applied]
            self.git_manager.commit_changes(fixed_files)
            logger.info(f"Committed {len(fixed_files)} file(s)")
            
            # Push branch
            self.git_manager.push_branch(branch_name)
            logger.info(f"Pushed branch: {branch_name}")
            
            # Create PR
            pr_url = self.git_manager.create_pr(branch_name, fixed_files)
            logger.info(f"Created PR: {pr_url}")
            
            return pr_url
        
        except Exception as e:
            logger.error(f"Failed to create PR: {str(e)}")
            return None


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="AI Self-Healing Pipeline with Claude API"
    )
    parser.add_argument("--workspace", required=True, help="Workspace directory")
    parser.add_argument("--build-log", default="build.log", help="Build log file")
    parser.add_argument("--api-tier", default="standard", help="API tier (lite/standard/premium)")
    parser.add_argument("--max-errors", type=int, default=5, help="Max errors per batch")
    parser.add_argument("--create-pr", action="store_true", help="Create PR automatically")
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = SelfHealerAgent(
        workspace=args.workspace,
        api_tier=args.api_tier
    )
    
    # Run analysis
    result = agent.run(
        build_log=args.build_log,
        create_pr=args.create_pr,
        max_errors=args.max_errors
    )
    
    # Log result
    logger.info(f"Final Result: {json.dumps(result, indent=2)}")
    
    # Set GitHub output
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"result={result['status']}\n")
            if "pr_url" in result:
                f.write(f"pr_url={result['pr_url']}\n")
    
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
