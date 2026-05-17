#!/usr/bin/env python3
"""
Error Parser Module

Extracts error information from:
- Maven surefire reports
- Build logs
- Stack traces

Provides structured error objects for analysis.
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Common error types in Java applications."""
    NPE = "NullPointerException"
    COMPILATION = "CompilationError"
    TEST_FAILURE = "TestFailure"
    TIMEOUT = "TimeoutException"
    DEPENDENCY = "DependencyIssue"
    IO = "IOException"
    ASSERTION = "AssertionError"
    UNKNOWN = "UnknownError"


@dataclass
class ErrorContext:
    """Structured representation of an error."""
    error_type: str
    error_message: str
    file_path: str
    line_number: int
    stack_trace: str
    source_context: str
    test_name: Optional[str] = None
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    
    def __str__(self):
        return f"{self.error_type} in {self.file_path}:{self.line_number}"


class ErrorBatch:
    """Batch of errors for processing."""
    
    def __init__(self, errors: List[ErrorContext]):
        self.errors = errors
        self.error_types = list(set(e.error_type for e in errors))
        self.files_affected = list(set(e.file_path for e in errors))
    
    def __len__(self):
        return len(self.errors)
    
    def to_dict(self):
        return {
            "count": len(self.errors),
            "error_types": self.error_types,
            "files_affected": self.files_affected
        }


class ErrorParser:
    """Parses errors from various sources."""
    
    # Regex patterns
    STACK_TRACE_PATTERN = re.compile(
        r'at ([\w\.]+)\(([\w$]+\.java):(\d+)\)',
        re.MULTILINE
    )
    
    NPE_PATTERN = re.compile(
        r'java\.lang\.NullPointerException',
        re.IGNORECASE
    )
    
    COMPILATION_ERROR_PATTERN = re.compile(
        r'\[ERROR\].*?\.java:\d+.*?(?:cannot find symbol|incompatible types|error:)',
        re.IGNORECASE
    )
    
    TEST_FAILURE_PATTERN = re.compile(
        r'(FAILURE|ERROR).*?(?:at |in )(\w+Test)',
        re.IGNORECASE
    )
    
    TIMEOUT_PATTERN = re.compile(
        r'(?:timeout|timed out|time out)',
        re.IGNORECASE
    )
    
    def parse_surefire_reports(self, surefire_dir: Path) -> List[ErrorContext]:
        """Parse Maven surefire test reports."""
        errors = []
        
        if not surefire_dir.exists():
            logger.warning(f"Surefire directory not found: {surefire_dir}")
            return errors
        
        # Find all test result files
        report_files = list(surefire_dir.glob("*.txt"))
        logger.info(f"Found {len(report_files)} surefire report files")
        
        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse report file
                file_errors = self._parse_surefire_content(content, report_file.name)
                errors.extend(file_errors)
                logger.info(f"Parsed {len(file_errors)} error(s) from {report_file.name}")
            
            except Exception as e:
                logger.error(f"Error parsing {report_file}: {str(e)}")
        
        return errors
    
    def parse_build_log(self, log_file: str) -> List[ErrorContext]:
        """Parse Maven build log for compilation errors."""
        errors = []
        
        if not Path(log_file).exists():
            logger.warning(f"Build log not found: {log_file}")
            return errors
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find compilation errors
            errors.extend(self._parse_compilation_errors(content))
            
            # Find test failures
            errors.extend(self._parse_test_failures(content))
        
        except Exception as e:
            logger.error(f"Error parsing build log: {str(e)}")
        
        return errors
    
    def _parse_surefire_content(self, content: str, filename: str) -> List[ErrorContext]:
        """Parse content of a surefire report file."""
        errors = []
        
        # Extract test name from filename
        test_name = filename.replace(".txt", "").replace("TEST-", "")
        
        # Look for error sections
        error_sections = content.split("Error Message:")
        
        for section in error_sections[1:]:  # Skip first split
            try:
                # Extract error message (first line)
                lines = section.strip().split('\n')
                error_message = lines[0][:200]
                
                # Find stack trace
                stack_trace_match = re.search(
                    r'Trace:\s*(.*?)(?:Error Message:|$)',
                    section,
                    re.DOTALL
                )
                
                if stack_trace_match:
                    stack_trace = stack_trace_match.group(1).strip()
                else:
                    stack_trace = section[:500]
                
                # Determine error type
                error_type = self._classify_error(error_message, stack_trace)
                
                # Extract file path and line number
                file_path, line_no = self._extract_file_location(stack_trace)
                
                # Get source context
                source_context = self._get_source_context(file_path, line_no)
                
                # Extract class and method names
                class_name, method_name = self._extract_class_method(stack_trace)
                
                error = ErrorContext(
                    error_type=error_type.value if isinstance(error_type, ErrorType) else error_type,
                    error_message=error_message,
                    file_path=file_path,
                    line_number=line_no,
                    stack_trace=stack_trace,
                    source_context=source_context,
                    test_name=test_name,
                    class_name=class_name,
                    method_name=method_name
                )
                
                errors.append(error)
                logger.debug(f"Parsed error: {error}")
            
            except Exception as e:
                logger.debug(f"Error parsing surefire section: {str(e)}")
        
        return errors
    
    def _parse_compilation_errors(self, content: str) -> List[ErrorContext]:
        """Extract compilation errors from build output."""
        errors = []
        
        # Find all compilation error lines
        error_lines = self.COMPILATION_ERROR_PATTERN.findall(content)
        
        for error_line in error_lines:
            try:
                # Extract file path
                match = re.search(r'\[(.+?\.java):(\d+)\]', error_line)
                if match:
                    file_path = match.group(1)
                    line_no = int(match.group(2))
                    
                    source_context = self._get_source_context(file_path, line_no)
                    
                    error = ErrorContext(
                        error_type=ErrorType.COMPILATION.value,
                        error_message=error_line,
                        file_path=file_path,
                        line_number=line_no,
                        stack_trace=error_line,
                        source_context=source_context,
                        test_name="Compilation"
                    )
                    
                    errors.append(error)
            
            except Exception as e:
                logger.debug(f"Error parsing compilation error: {str(e)}")
        
        return errors
    
    def _parse_test_failures(self, content: str) -> List[ErrorContext]:
        """Extract test failures from build output."""
        errors = []
        
        # Split by test failure markers
        failure_sections = re.split(
            r'\n\s*(?:FAILURE|ERROR|Failed tests|Tests run:)',
            content
        )
        
        for section in failure_sections[1:]:
            try:
                # Extract stack trace from section
                stack_match = re.search(
                    r'at [\w\.]+ \(.+?\.java:\d+\)',
                    section
                )
                
                if stack_match:
                    stack_trace = section[:1000]
                    
                    # Determine error type
                    error_type = self._classify_error("Test Failure", section)
                    
                    # Extract file info
                    file_path, line_no = self._extract_file_location(stack_trace)
                    
                    source_context = self._get_source_context(file_path, line_no)
                    
                    # Extract test name
                    test_match = re.search(r'(\w+Test)\s+', section)
                    test_name = test_match.group(1) if test_match else "Unknown"
                    
                    class_name, method_name = self._extract_class_method(stack_trace)
                    
                    error = ErrorContext(
                        error_type=error_type.value if isinstance(error_type, ErrorType) else error_type,
                        error_message="Test Failure",
                        file_path=file_path,
                        line_number=line_no,
                        stack_trace=stack_trace,
                        source_context=source_context,
                        test_name=test_name,
                        class_name=class_name,
                        method_name=method_name
                    )
                    
                    errors.append(error)
            
            except Exception as e:
                logger.debug(f"Error parsing test failure: {str(e)}")
        
        return errors
    
    def _classify_error(self, message: str, stack_trace: str) -> ErrorType:
        """Classify error type from message and stack trace."""
        combined = (message + " " + stack_trace).lower()
        
        if "nullpointerexception" in combined:
            return ErrorType.NPE
        elif "compilation" in combined or "error:" in combined:
            return ErrorType.COMPILATION
        elif "timeout" in combined:
            return ErrorType.TIMEOUT
        elif "dependency" in combined or "not found" in combined:
            return ErrorType.DEPENDENCY
        elif "ioexception" in combined:
            return ErrorType.IO
        elif "assertionerror" in combined:
            return ErrorType.ASSERTION
        elif "test" in combined:
            return ErrorType.TEST_FAILURE
        else:
            return ErrorType.UNKNOWN
    
    def _extract_file_location(self, stack_trace: str) -> tuple:
        """Extract file path and line number from stack trace."""
        matches = self.STACK_TRACE_PATTERN.findall(stack_trace)
        
        if matches:
            # Take the first user code match
            for match in matches:
                class_path = match[0]
                file_name = match[1]
                line_num = int(match[2])
                
                # Convert class path to file path
                file_path = self._class_to_file_path(class_path, file_name)
                
                return file_path, line_num
        
        return "unknown.java", 0
    
    def _class_to_file_path(self, class_path: str, file_name: str) -> str:
        """Convert class path to file path."""
        # Extract package
        parts = class_path.rsplit(".", 1)
        if len(parts) == 2:
            package = parts[0]
            package_path = package.replace(".", "/")
            return f"src/main/java/{package_path}/{file_name}"
        return f"src/main/java/{file_name}"
    
    def _extract_class_method(self, stack_trace: str) -> tuple:
        """Extract class and method names from stack trace."""
        match = self.STACK_TRACE_PATTERN.search(stack_trace)
        
        if match:
            full_method = match.group(1)
            parts = full_method.rsplit(".", 1)
            
            if len(parts) == 2:
                class_name = parts[0]
                method_name = parts[1]
                return class_name, method_name
        
        return None, None
    
    def _get_source_context(self, file_path: str, line_number: int, context_lines: int = 3) -> str:
        """Read source file context around error line."""
        try:
            if not Path(file_path).exists():
                # Try to find the file
                found_path = self._search_file(file_path)
                if not found_path:
                    return f"File not found: {file_path}"
                file_path = str(found_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            context = "".join(lines[start:end])
            return context
        
        except Exception as e:
            return f"Could not read context: {str(e)}"
    
    def _search_file(self, file_path: str) -> Optional[Path]:
        """Search for file in project directories."""
        file_name = Path(file_path).name
        
        for root_dir in ["src", "target"]:
            if Path(root_dir).exists():
                for found_path in Path(root_dir).rglob(file_name):
                    return found_path
        
        return None
