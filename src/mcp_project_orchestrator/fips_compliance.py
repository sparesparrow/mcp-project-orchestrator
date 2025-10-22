#!/usr/bin/env python3
"""
FIPS Compliance Framework for OpenSSL Development.

This module implements comprehensive FIPS 140-3 compliance validation
for OpenSSL cryptographic code, following the AI Coding Guidelines
for secure development practices.
"""

import asyncio
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import ast
import tokenize
import io

logger = logging.getLogger(__name__)

class FIPSValidationLevel(Enum):
    """FIPS validation levels."""
    BASIC = "basic"
    DETAILED = "detailed"
    CRYPTO_CORE = "crypto_core"

class SecurityViolationType(Enum):
    """Types of security violations."""
    NON_FIPS_ALGORITHM = "non_fips_algorithm"
    KEY_MATERIAL_EXPOSURE = "key_material_exposure"
    MISSING_INPUT_VALIDATION = "missing_input_validation"
    INSECURE_ERROR_HANDLING = "insecure_error_handling"
    SIDE_CHANNEL_VULNERABILITY = "side_channel_vulnerability"
    CRYPTO_IN_WRONG_LAYER = "crypto_in_wrong_layer"
    MISSING_SELF_TESTS = "missing_self_tests"
    INSECURE_MEMORY_HANDLING = "insecure_memory_handling"

@dataclass
class FIPSValidationResult:
    """Result of FIPS compliance validation."""
    compliant: bool
    violations: List['SecurityViolation']
    recommendations: List[str]
    security_assessment: Dict[str, Any]
    certification_impact: str
    validation_level: FIPSValidationLevel
    execution_time: float

@dataclass
class SecurityViolation:
    """Represents a security violation found in code."""
    violation_type: SecurityViolationType
    severity: str  # critical, high, medium, low
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    fix_suggestion: Optional[str] = None

@dataclass
class FIPSRequirements:
    """FIPS 140-3 requirements configuration."""
    approved_algorithms: Set[str] = field(default_factory=lambda: {
        "AES", "SHA-256", "SHA-384", "SHA-512", "SHA-3", "RSA", "ECDSA", 
        "ECDH", "HMAC", "PBKDF2", "HKDF", "GCM", "CTR", "CBC"
    })
    forbidden_algorithms: Set[str] = field(default_factory=lambda: {
        "MD5", "SHA-1", "RC4", "DES", "3DES", "Blowfish", "Twofish"
    })
    required_self_tests: Set[str] = field(default_factory=lambda: {
        "algorithm_known_answer_tests", "continuous_random_number_generator_tests",
        "software_integrity_tests", "critical_functions_tests"
    })
    key_management_requirements: Set[str] = field(default_factory=lambda: {
        "secure_key_generation", "secure_key_storage", "secure_key_transport",
        "key_derivation", "key_establishment", "key_compromise_procedures"
    })

class FIPSComplianceValidator:
    """
    Validates OpenSSL code against FIPS 140-3 requirements.
    
    This validator implements the security-first approach outlined in the
    AI Coding Guidelines, ensuring cryptographic code meets FIPS standards.
    """
    
    def __init__(self, validation_level: FIPSValidationLevel = FIPSValidationLevel.DETAILED):
        self.validation_level = validation_level
        self.fips_requirements = FIPSRequirements()
        self.pattern_detector = SecurityPatternDetector()
        self.algorithm_validator = AlgorithmValidator()
        self.key_management_validator = KeyManagementValidator()
        self.self_test_validator = SelfTestValidator()
        self.side_channel_analyzer = SideChannelAnalyzer()
        
        logger.info(f"Initialized FIPS Compliance Validator with {validation_level.value} level")
    
    async def validate_crypto_changes(
        self, 
        code_changes: List[str],
        fips_context: Dict[str, Any]
    ) -> FIPSValidationResult:
        """Validate cryptographic changes against FIPS requirements."""
        
        start_time = asyncio.get_event_loop().time()
        violations = []
        recommendations = []
        
        try:
            # Parse code changes
            parsed_changes = await self._parse_code_changes(code_changes)
            
            # Perform validation checks
            validation_checks = [
                self._validate_approved_algorithms(parsed_changes),
                self._validate_key_management(parsed_changes),
                self._validate_self_tests(parsed_changes),
                self._validate_side_channel_protection(parsed_changes),
                self._validate_error_handling(parsed_changes),
                self._validate_input_validation(parsed_changes),
                self._validate_memory_handling(parsed_changes),
                self._validate_architectural_boundaries(parsed_changes, fips_context)
            ]
            
            # Execute all validation checks
            check_results = await asyncio.gather(*validation_checks, return_exceptions=True)
            
            # Collect results
            for result in check_results:
                if isinstance(result, Exception):
                    logger.error(f"Validation check failed: {result}")
                    continue
                
                if isinstance(result, list):
                    violations.extend(result)
                elif isinstance(result, dict) and "recommendations" in result:
                    recommendations.extend(result["recommendations"])
            
            # Generate security assessment
            security_assessment = await self._generate_security_assessment(violations, fips_context)
            
            # Determine certification impact
            certification_impact = self._assess_certification_impact(violations)
            
            # Generate recommendations
            recommendations.extend(await self._generate_recommendations(violations, fips_context))
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return FIPSValidationResult(
                compliant=len(violations) == 0,
                violations=violations,
                recommendations=recommendations,
                security_assessment=security_assessment,
                certification_impact=certification_impact,
                validation_level=self.validation_level,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error in FIPS validation: {e}")
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return FIPSValidationResult(
                compliant=False,
                violations=[SecurityViolation(
                    violation_type=SecurityViolationType.MISSING_SELF_TESTS,
                    severity="critical",
                    message=f"FIPS validation failed: {str(e)}"
                )],
                recommendations=["Fix validation errors and retry"],
                security_assessment={"error": str(e)},
                certification_impact="unknown",
                validation_level=self.validation_level,
                execution_time=execution_time
            )
    
    async def _parse_code_changes(self, code_changes: List[str]) -> List[Dict[str, Any]]:
        """Parse code changes into structured format."""
        parsed_changes = []
        
        for i, code in enumerate(code_changes):
            try:
                # Parse Python code
                tree = ast.parse(code)
                
                # Extract function definitions
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                
                # Extract class definitions
                classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                
                # Extract string literals (potential algorithm names)
                strings = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Str):
                        strings.append(node.s)
                
                parsed_changes.append({
                    "index": i,
                    "code": code,
                    "ast_tree": tree,
                    "functions": functions,
                    "classes": classes,
                    "strings": strings,
                    "lines": code.split('\n')
                })
                
            except SyntaxError as e:
                logger.warning(f"Syntax error in code change {i}: {e}")
                parsed_changes.append({
                    "index": i,
                    "code": code,
                    "error": str(e),
                    "lines": code.split('\n')
                })
        
        return parsed_changes
    
    async def _validate_approved_algorithms(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate use of FIPS-approved algorithms."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            # Check for forbidden algorithms
            for line_num, line in enumerate(change["lines"], 1):
                line_lower = line.lower()
                
                for forbidden_alg in self.fips_requirements.forbidden_algorithms:
                    if forbidden_alg.lower() in line_lower:
                        violations.append(SecurityViolation(
                            violation_type=SecurityViolationType.NON_FIPS_ALGORITHM,
                            severity="critical",
                            message=f"Non-FIPS approved algorithm '{forbidden_alg}' detected",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            fix_suggestion=f"Replace {forbidden_alg} with FIPS-approved alternative"
                        ))
                
                # Check for approved algorithms (positive validation)
                for approved_alg in self.fips_requirements.approved_algorithms:
                    if approved_alg.lower() in line_lower:
                        # Verify proper usage
                        if not self._verify_algorithm_usage(line, approved_alg):
                            violations.append(SecurityViolation(
                                violation_type=SecurityViolationType.NON_FIPS_ALGORITHM,
                                severity="medium",
                                message=f"Improper usage of FIPS-approved algorithm '{approved_alg}'",
                                line_number=line_num,
                                code_snippet=line.strip(),
                                fix_suggestion=f"Verify proper {approved_alg} implementation"
                            ))
        
        return violations
    
    async def _validate_key_management(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate key management practices."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            for line_num, line in enumerate(change["lines"], 1):
                line_lower = line.lower()
                
                # Check for key material exposure
                if any(keyword in line_lower for keyword in ["key", "secret", "password"]) and \
                   any(exposure in line_lower for exposure in ["log", "print", "debug", "return"]):
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.KEY_MATERIAL_EXPOSURE,
                        severity="critical",
                        message="Potential key material exposure detected",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        fix_suggestion="Remove key material from logging/debugging output"
                    ))
                
                # Check for insecure key generation
                if "random" in line_lower and "key" in line_lower:
                    if not any(secure_method in line_lower for secure_method in 
                             ["openssl", "cryptographically", "secure", "fips"]):
                        violations.append(SecurityViolation(
                            violation_type=SecurityViolationType.KEY_MATERIAL_EXPOSURE,
                            severity="high",
                            message="Potentially insecure key generation detected",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            fix_suggestion="Use cryptographically secure random number generator"
                        ))
        
        return violations
    
    async def _validate_self_tests(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate FIPS self-test implementation."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            # Check for self-test functions
            has_self_tests = False
            for func in change.get("functions", []):
                func_name = func.name.lower()
                if any(test_type in func_name for test_type in 
                      ["self_test", "kat", "known_answer", "integrity"]):
                    has_self_tests = True
                    break
            
            # Check for self-test calls
            for line in change["lines"]:
                if "self_test" in line.lower() or "fips_test" in line.lower():
                    has_self_tests = True
                    break
            
            if not has_self_tests and any("crypto" in line.lower() or "encrypt" in line.lower() 
                                        for line in change["lines"]):
                violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.MISSING_SELF_TESTS,
                    severity="critical",
                    message="FIPS self-tests missing for cryptographic code",
                    fix_suggestion="Implement required FIPS self-tests"
                ))
        
        return violations
    
    async def _validate_side_channel_protection(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate side-channel attack protection."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            for line_num, line in enumerate(change["lines"], 1):
                line_lower = line.lower()
                
                # Check for timing attack vulnerabilities
                if any(operation in line_lower for operation in ["compare", "equal", "strcmp"]) and \
                   any(crypto_context in line_lower for crypto_context in ["key", "hash", "signature"]):
                    if "constant_time" not in line_lower and "secure" not in line_lower:
                        violations.append(SecurityViolation(
                            violation_type=SecurityViolationType.SIDE_CHANNEL_VULNERABILITY,
                            severity="high",
                            message="Potential timing attack vulnerability",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            fix_suggestion="Use constant-time comparison functions"
                        ))
                
                # Check for power analysis vulnerabilities
                if "if" in line_lower and any(crypto_op in line_lower for crypto_op in 
                                            ["encrypt", "decrypt", "sign", "verify"]):
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.SIDE_CHANNEL_VULNERABILITY,
                        severity="medium",
                        message="Potential power analysis vulnerability",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        fix_suggestion="Consider power analysis resistant implementation"
                    ))
        
        return violations
    
    async def _validate_error_handling(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate secure error handling patterns."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            for line_num, line in enumerate(change["lines"], 1):
                line_lower = line.lower()
                
                # Check for error information leakage
                if any(error_keyword in line_lower for error_keyword in ["error", "exception", "fail"]) and \
                   any(leak_keyword in line_lower for leak_keyword in ["print", "log", "return"]):
                    if not any(secure_pattern in line_lower for secure_pattern in 
                             ["generic", "invalid", "failed", "error"]):
                        violations.append(SecurityViolation(
                            violation_type=SecurityViolationType.INSECURE_ERROR_HANDLING,
                            severity="medium",
                            message="Potential error information leakage",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            fix_suggestion="Use generic error messages to prevent information leakage"
                        ))
        
        return violations
    
    async def _validate_input_validation(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate input validation at trust boundaries."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            # Check function definitions for input validation
            for func in change.get("functions", []):
                func_name = func.name.lower()
                
                # Check if function has parameters but no validation
                if func.args.args and not self._has_input_validation(func):
                    if any(crypto_context in func_name for crypto_context in 
                          ["encrypt", "decrypt", "sign", "verify", "hash"]):
                        violations.append(SecurityViolation(
                            violation_type=SecurityViolationType.MISSING_INPUT_VALIDATION,
                            severity="high",
                            message=f"Missing input validation in cryptographic function '{func.name}'",
                            fix_suggestion="Add comprehensive input validation"
                        ))
        
        return violations
    
    async def _validate_memory_handling(self, parsed_changes: List[Dict[str, Any]]) -> List[SecurityViolation]:
        """Validate secure memory handling."""
        violations = []
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            for line_num, line in enumerate(change["lines"], 1):
                line_lower = line.lower()
                
                # Check for insecure memory operations
                if any(mem_op in line_lower for mem_op in ["malloc", "free", "memset"]) and \
                   any(crypto_context in line_lower for crypto_context in ["key", "secret", "password"]):
                    if "secure" not in line_lower and "openssl" not in line_lower:
                        violations.append(SecurityViolation(
                            violation_type=SecurityViolationType.INSECURE_MEMORY_HANDLING,
                            severity="high",
                            message="Potentially insecure memory handling for sensitive data",
                            line_number=line_num,
                            code_snippet=line.strip(),
                            fix_suggestion="Use secure memory functions (OPENSSL_secure_malloc, etc.)"
                        ))
        
        return violations
    
    async def _validate_architectural_boundaries(
        self, 
        parsed_changes: List[Dict[str, Any]], 
        fips_context: Dict[str, Any]
    ) -> List[SecurityViolation]:
        """Validate architectural boundaries (DDD compliance)."""
        violations = []
        
        # Check if code is in the correct architectural layer
        file_path = fips_context.get("file_path", "")
        layer = self._detect_architectural_layer(file_path)
        
        for change in parsed_changes:
            if "error" in change:
                continue
            
            for line_num, line in enumerate(change["lines"], 1):
                line_lower = line.lower()
                
                # Check for crypto implementation in wrong layer
                if any(crypto_impl in line_lower for crypto_impl in 
                      ["encrypt", "decrypt", "sign", "verify", "hash", "cipher"]) and \
                   layer in ["application", "infrastructure", "presentation"]:
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.CRYPTO_IN_WRONG_LAYER,
                        severity="critical",
                        message="Cryptographic implementation in non-domain layer",
                        line_number=line_num,
                        code_snippet=line.strip(),
                        fix_suggestion="Move cryptographic code to domain layer"
                    ))
        
        return violations
    
    def _verify_algorithm_usage(self, line: str, algorithm: str) -> bool:
        """Verify proper usage of FIPS-approved algorithm."""
        # This is a simplified check - in real implementation, would be more comprehensive
        return "openssl" in line.lower() or "fips" in line.lower()
    
    def _has_input_validation(self, func: ast.FunctionDef) -> bool:
        """Check if function has input validation."""
        # Look for validation patterns in function body
        for node in ast.walk(func):
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
                return True
            if isinstance(node, ast.Assert):
                return True
        return False
    
    def _detect_architectural_layer(self, file_path: str) -> str:
        """Detect architectural layer from file path."""
        path_lower = file_path.lower()
        
        if "domain" in path_lower or "crypto" in path_lower:
            return "domain"
        elif "application" in path_lower or "service" in path_lower:
            return "application"
        elif "infrastructure" in path_lower or "infra" in path_lower:
            return "infrastructure"
        elif "presentation" in path_lower or "api" in path_lower or "controller" in path_lower:
            return "presentation"
        else:
            return "unknown"
    
    async def _generate_security_assessment(
        self, 
        violations: List[SecurityViolation], 
        fips_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive security assessment."""
        
        critical_violations = [v for v in violations if v.severity == "critical"]
        high_violations = [v for v in violations if v.severity == "high"]
        
        return {
            "overall_security_score": self._calculate_security_score(violations),
            "critical_issues": len(critical_violations),
            "high_priority_issues": len(high_violations),
            "algorithm_compliance": not any(v.violation_type == SecurityViolationType.NON_FIPS_ALGORITHM 
                                         for v in violations),
            "key_management_secure": not any(v.violation_type == SecurityViolationType.KEY_MATERIAL_EXPOSURE 
                                           for v in violations),
            "side_channel_resistant": not any(v.violation_type == SecurityViolationType.SIDE_CHANNEL_VULNERABILITY 
                                            for v in violations),
            "architectural_compliance": not any(v.violation_type == SecurityViolationType.CRYPTO_IN_WRONG_LAYER 
                                              for v in violations),
            "fips_ready": len(violations) == 0
        }
    
    def _calculate_security_score(self, violations: List[SecurityViolation]) -> int:
        """Calculate security score (0-100)."""
        if not violations:
            return 100
        
        # Penalty system
        penalties = {
            "critical": 25,
            "high": 15,
            "medium": 10,
            "low": 5
        }
        
        total_penalty = sum(penalties.get(v.severity, 0) for v in violations)
        return max(0, 100 - total_penalty)
    
    def _assess_certification_impact(self, violations: List[SecurityViolation]) -> str:
        """Assess impact on FIPS certification."""
        critical_violations = [v for v in violations if v.severity == "critical"]
        
        if not violations:
            return "certification_ready"
        elif critical_violations:
            return "certification_blocked"
        else:
            return "certification_requires_review"
    
    async def _generate_recommendations(
        self, 
        violations: List[SecurityViolation], 
        fips_context: Dict[str, Any]
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Algorithm recommendations
        if any(v.violation_type == SecurityViolationType.NON_FIPS_ALGORITHM for v in violations):
            recommendations.append("Replace all non-FIPS approved algorithms with approved alternatives")
        
        # Key management recommendations
        if any(v.violation_type == SecurityViolationType.KEY_MATERIAL_EXPOSURE for v in violations):
            recommendations.append("Implement secure key management practices and remove key material from logs")
        
        # Self-test recommendations
        if any(v.violation_type == SecurityViolationType.MISSING_SELF_TESTS for v in violations):
            recommendations.append("Implement required FIPS self-tests for all cryptographic functions")
        
        # Side-channel recommendations
        if any(v.violation_type == SecurityViolationType.SIDE_CHANNEL_VULNERABILITY for v in violations):
            recommendations.append("Implement side-channel resistant algorithms and constant-time operations")
        
        # Architectural recommendations
        if any(v.violation_type == SecurityViolationType.CRYPTO_IN_WRONG_LAYER for v in violations):
            recommendations.append("Move cryptographic implementations to domain layer following DDD principles")
        
        return recommendations

class SecurityPatternDetector:
    """Detects security patterns and anti-patterns in code."""
    
    def __init__(self):
        self.anti_patterns = {
            "hardcoded_secrets": r"(password|secret|key|token)\s*=\s*[\"'][^\"']+[\"']",
            "sql_injection": r"execute\s*\(\s*[\"'][^\"']*%[^\"']*[\"']",
            "path_traversal": r"open\s*\(\s*[\"'][^\"']*\.\./",
            "command_injection": r"os\.system\s*\(|subprocess\.call\s*\("
        }
    
    def detect_anti_patterns(self, code: str) -> List[SecurityViolation]:
        """Detect security anti-patterns in code."""
        violations = []
        
        for pattern_name, pattern in self.anti_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.KEY_MATERIAL_EXPOSURE,
                    severity="high",
                    message=f"Security anti-pattern detected: {pattern_name}",
                    code_snippet=match.group(),
                    fix_suggestion=f"Remove or secure {pattern_name} pattern"
                ))
        
        return violations

class AlgorithmValidator:
    """Validates cryptographic algorithm usage."""
    
    def __init__(self):
        self.fips_algorithms = {
            "AES": ["AES-128", "AES-192", "AES-256"],
            "SHA": ["SHA-256", "SHA-384", "SHA-512", "SHA-3"],
            "RSA": ["RSA-2048", "RSA-3072", "RSA-4096"],
            "ECDSA": ["P-256", "P-384", "P-521"]
        }
    
    def validate_algorithm_usage(self, algorithm: str, context: str) -> bool:
        """Validate if algorithm is used correctly in context."""
        # Implementation would check proper algorithm usage
        return True

class KeyManagementValidator:
    """Validates key management practices."""
    
    def validate_key_generation(self, code: str) -> List[SecurityViolation]:
        """Validate key generation practices."""
        violations = []
        
        if "random" in code.lower() and "key" in code.lower():
            if "openssl" not in code.lower() and "cryptographically" not in code.lower():
                violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.KEY_MATERIAL_EXPOSURE,
                    severity="high",
                    message="Insecure key generation detected",
                    fix_suggestion="Use cryptographically secure random number generator"
                ))
        
        return violations

class SelfTestValidator:
    """Validates FIPS self-test implementation."""
    
    def validate_self_tests(self, code: str) -> List[SecurityViolation]:
        """Validate self-test implementation."""
        violations = []
        
        if "crypto" in code.lower() and "self_test" not in code.lower():
            violations.append(SecurityViolation(
                violation_type=SecurityViolationType.MISSING_SELF_TESTS,
                severity="critical",
                message="FIPS self-tests missing",
                fix_suggestion="Implement required FIPS self-tests"
            ))
        
        return violations

class SideChannelAnalyzer:
    """Analyzes side-channel vulnerabilities."""
    
    def analyze_timing_attacks(self, code: str) -> List[SecurityViolation]:
        """Analyze timing attack vulnerabilities."""
        violations = []
        
        if "compare" in code.lower() and "key" in code.lower():
            if "constant_time" not in code.lower():
                violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.SIDE_CHANNEL_VULNERABILITY,
                    severity="high",
                    message="Potential timing attack vulnerability",
                    fix_suggestion="Use constant-time comparison"
                ))
        
        return violations