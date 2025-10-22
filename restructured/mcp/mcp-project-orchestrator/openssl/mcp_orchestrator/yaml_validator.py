"""
YAML frontmatter validation for Cursor rule files.

This module provides validation for YAML frontmatter in .mdc files
to ensure they follow the repository standard.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of YAML frontmatter validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    frontmatter: Optional[Dict[str, Any]] = None


class YAMLFrontmatterValidator:
    """Validates YAML frontmatter in .mdc files."""
    
    REQUIRED_FIELDS = {
        "title": str,
        "description": str,
        "created": str,
        "platform": str,
        "user": str,
    }
    
    OPTIONAL_FIELDS = {
        "version": str,
        "author": str,
        "tags": list,
        "deprecated": bool,
    }
    
    VALID_PLATFORMS = {
        "shared", "linux", "macos", "windows", "ci-linux", "ci-macos", "ci-windows"
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate YAML frontmatter in a .mdc file.
        
        Args:
            file_path: Path to the .mdc file to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        self.errors.clear()
        self.warnings.clear()
        
        if not file_path.exists():
            self.errors.append(f"File does not exist: {file_path}")
            return ValidationResult(False, self.errors.copy(), self.warnings.copy())
        
        if not file_path.suffix == '.mdc':
            self.errors.append(f"File is not a .mdc file: {file_path}")
            return ValidationResult(False, self.errors.copy(), self.warnings.copy())
        
        try:
            content = file_path.read_text(encoding='utf-8')
            frontmatter = self._extract_frontmatter(content)
            
            if frontmatter is None:
                self.errors.append("No YAML frontmatter found")
                return ValidationResult(False, self.errors.copy(), self.warnings.copy())
            
            # Validate frontmatter content
            self._validate_frontmatter(frontmatter, file_path)
            
            is_valid = len(self.errors) == 0
            return ValidationResult(
                is_valid=is_valid,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
                frontmatter=frontmatter
            )
            
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return ValidationResult(False, self.errors.copy(), self.warnings.copy())
    
    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract YAML frontmatter from file content."""
        # Look for YAML frontmatter between --- markers
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        
        if not match:
            return None
        
        yaml_content = match.group(1)
        
        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax: {e}")
            return None
    
    def _validate_frontmatter(self, frontmatter: Dict[str, Any], file_path: Path) -> None:
        """Validate frontmatter content against schema."""
        # Check required fields
        for field, field_type in self.REQUIRED_FIELDS.items():
            if field not in frontmatter:
                self.errors.append(f"Missing required field: {field}")
            elif not isinstance(frontmatter[field], field_type):
                self.errors.append(f"Field '{field}' must be of type {field_type.__name__}")
        
        # Check optional fields
        for field, field_type in self.OPTIONAL_FIELDS.items():
            if field in frontmatter and not isinstance(frontmatter[field], field_type):
                self.warnings.append(f"Field '{field}' should be of type {field_type.__name__}")
        
        # Validate platform field
        if "platform" in frontmatter:
            platform = frontmatter["platform"]
            if platform not in self.VALID_PLATFORMS:
                self.errors.append(f"Invalid platform '{platform}'. Must be one of: {', '.join(self.VALID_PLATFORMS)}")
        
        # Validate created field format (should be ISO format)
        if "created" in frontmatter:
            created = frontmatter["created"]
            if not self._is_valid_iso_date(created):
                self.warnings.append(f"Field 'created' should be in ISO format: {created}")
        
        # Check for unknown fields
        all_valid_fields = set(self.REQUIRED_FIELDS.keys()) | set(self.OPTIONAL_FIELDS.keys())
        unknown_fields = set(frontmatter.keys()) - all_valid_fields
        if unknown_fields:
            self.warnings.append(f"Unknown fields found: {', '.join(unknown_fields)}")
    
    def _is_valid_iso_date(self, date_str: str) -> bool:
        """Check if date string is in valid ISO format."""
        try:
            from datetime import datetime
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def validate_directory(self, directory: Path) -> Dict[str, ValidationResult]:
        """
        Validate all .mdc files in a directory.
        
        Args:
            directory: Directory containing .mdc files
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        
        if not directory.exists():
            return results
        
        for mdc_file in directory.rglob("*.mdc"):
            results[str(mdc_file)] = self.validate_file(mdc_file)
        
        return results
    
    def validate_cursor_rules(self, cursor_dir: Path) -> Dict[str, ValidationResult]:
        """
        Validate all .mdc files in a .cursor directory structure.
        
        Args:
            cursor_dir: Path to .cursor directory
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        
        # Validate rules directory
        rules_dir = cursor_dir / "rules"
        if rules_dir.exists():
            rules_results = self.validate_directory(rules_dir)
            results.update(rules_results)
        
        return results


def validate_cursor_configuration(cursor_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate a complete Cursor configuration directory.
    
    Args:
        cursor_dir: Path to .cursor directory
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = YAMLFrontmatterValidator()
    results = validator.validate_cursor_rules(cursor_dir)
    
    all_valid = True
    all_errors = []
    
    for file_path, result in results.items():
        if not result.is_valid:
            all_valid = False
            all_errors.append(f"Validation failed for {file_path}:")
            all_errors.extend(f"  - {error}" for error in result.errors)
            all_errors.append("")
    
    return all_valid, all_errors


def main():
    """CLI entry point for YAML validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate YAML frontmatter in .mdc files")
    parser.add_argument("path", help="Path to .mdc file or directory containing .mdc files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show warnings")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    validator = YAMLFrontmatterValidator()
    
    if path.is_file():
        result = validator.validate_file(path)
        print(f"Validating: {path}")
        print(f"Valid: {result.is_valid}")
        
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        if args.verbose and result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
    
    elif path.is_dir():
        results = validator.validate_directory(path)
        
        print(f"Validating directory: {path}")
        print(f"Found {len(results)} .mdc files")
        
        valid_count = sum(1 for r in results.values() if r.is_valid)
        print(f"Valid files: {valid_count}/{len(results)}")
        
        for file_path, result in results.items():
            if not result.is_valid:
                print(f"\n❌ {file_path}:")
                for error in result.errors:
                    print(f"  - {error}")
            elif args.verbose and result.warnings:
                print(f"\n⚠️  {file_path}:")
                for warning in result.warnings:
                    print(f"  - {warning}")
    
    else:
        print(f"Error: {path} is not a file or directory")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())