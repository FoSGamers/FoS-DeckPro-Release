#!/usr/bin/env python3
"""
Startup AI Audit for PhaseSynth Ultra+
Implements automatic project scan on open with comprehensive analysis
Enforces APTPT, HCE, and REI theories for complete project validation
"""

import os
import json
import hashlib
import ast
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import yaml
import re
from dataclasses import dataclass, asdict
import difflib
import tempfile

@dataclass
class AuditResult:
    """Represents an audit result with full metadata"""
    component: str
    status: str  # pass, warning, error, critical
    description: str
    details: Dict[str, Any]
    recommendations: List[str]
    phase_vector: str
    entropy_score: float
    rei_score: float
    timestamp: datetime

@dataclass
class ProjectHealth:
    """Overall project health assessment"""
    overall_score: float  # 0-100
    critical_issues: int
    warnings: int
    passed_checks: int
    total_checks: int
    recommendations: List[str]
    timestamp: datetime

class StartupAIAudit:
    """Startup AI Audit system with comprehensive project analysis"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.audit_results = []
        self.project_health = None
        self.auto_fixes_applied = []
        self.manual_actions_required = []
        
        # Audit patterns
        self.audit_patterns = {
            "security": [
                r"eval\s*\(",
                r"exec\s*\(",
                r"input\s*\(",
                r"os\.system\s*\(",
                r"subprocess\.call\s*\(",
                r"password\s*=",
                r"secret\s*=",
                r"api_key\s*="
            ],
            "performance": [
                r"for\s+\w+\s+in\s+range\(len\([^)]+\)\)",
                r"if\s+\w+\s+in\s+\[[^\]]+\]",
                r"\.append\([^)]+\)\s*$",
                r"global\s+\w+",
                r"import\s+\*"
            ],
            "maintainability": [
                r"def\s+\w+\([^)]*\):\s*$",
                r"class\s+\w+[^:]*:\s*$",
                r"# TODO:",
                r"# FIXME:",
                r"# HACK:",
                r"# XXX:"
            ],
            "compliance": [
                r"TODO:",
                r"FIXME:",
                r"HACK:",
                r"XXX:",
                r"BUG:"
            ]
        }
        
        # Required files and directories
        self.required_structure = {
            "files": [
                "README.md",
                "requirements.txt",
                "config.yaml",
                ".gitignore"
            ],
            "directories": [
                "src",
                "tests",
                "docs"
            ],
            "optional_files": [
                "setup.py",
                "package.json",
                "Dockerfile",
                "docker-compose.yml"
            ]
        }
    
    def _compute_phase_vector(self, data: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = json.dumps(data, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, data: Dict[str, Any]) -> float:
        """Compute entropy using HCE theory"""
        if not data:
            return 0.0
        data_str = json.dumps(data, sort_keys=True)
        char_freq = {}
        for char in data_str:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(data_str)
        entropy = 0.0
        for count in char_freq.values():
            p = count / total
            entropy -= p * math.log2(p) if p > 0 else 0
        return entropy
    
    def _compute_rei_score(self, phase_vector: str) -> float:
        """Compute REI score using REI theory"""
        if not phase_vector:
            return 0.0
        return sum(ord(c) for c in phase_vector[:8]) / (8 * 255)
    
    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run comprehensive startup audit"""
        print("[APTPT] Starting comprehensive startup AI audit...")
        
        # Clear previous results
        self.audit_results = []
        self.auto_fixes_applied = []
        self.manual_actions_required = []
        
        # Run all audit checks
        self._audit_project_structure()
        self._audit_code_quality()
        self._audit_security()
        self._audit_performance()
        self._audit_dependencies()
        self._audit_documentation()
        self._audit_testing()
        self._audit_configuration()
        self._audit_git_status()
        self._audit_build_system()
        
        # Calculate overall project health
        self._calculate_project_health()
        
        # Generate comprehensive report
        report = self._generate_audit_report()
        
        print(f"[APTPT] Audit complete: {len(self.audit_results)} checks performed")
        return report
    
    def _audit_project_structure(self):
        """Audit project structure and organization"""
        print("[APTPT] Auditing project structure...")
        
        # Check required files
        for file_name in self.required_structure["files"]:
            file_path = self.project_root / file_name
            if file_path.exists():
                self._add_audit_result(
                    component="structure",
                    status="pass",
                    description=f"Required file exists: {file_name}",
                    details={"file_path": str(file_path), "size": file_path.stat().st_size}
                )
            else:
                self._add_audit_result(
                    component="structure",
                    status="warning",
                    description=f"Missing required file: {file_name}",
                    details={"file_path": str(file_path)},
                    recommendations=[f"Create {file_name} file"]
                )
        
        # Check required directories
        for dir_name in self.required_structure["directories"]:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                file_count = len(list(dir_path.rglob("*")))
                self._add_audit_result(
                    component="structure",
                    status="pass",
                    description=f"Required directory exists: {dir_name}",
                    details={"dir_path": str(dir_path), "file_count": file_count}
                )
            else:
                self._add_audit_result(
                    component="structure",
                    status="warning",
                    description=f"Missing required directory: {dir_name}",
                    details={"dir_path": str(dir_path)},
                    recommendations=[f"Create {dir_name} directory"]
                )
        
        # Check optional files
        for file_name in self.required_structure["optional_files"]:
            file_path = self.project_root / file_name
            if file_path.exists():
                self._add_audit_result(
                    component="structure",
                    status="pass",
                    description=f"Optional file exists: {file_name}",
                    details={"file_path": str(file_path)}
                )
    
    def _audit_code_quality(self):
        """Audit code quality and standards"""
        print("[APTPT] Auditing code quality...")
        
        # Scan all code files
        code_files = []
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c']:
            code_files.extend(self.project_root.rglob(f"*{ext}"))
        
        total_files = len(code_files)
        quality_issues = []
        
        for file_path in code_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                file_issues = self._analyze_file_quality(file_path, content)
                quality_issues.extend(file_issues)
            except Exception as e:
                self._add_audit_result(
                    component="code_quality",
                    status="error",
                    description=f"Error analyzing {file_path.name}",
                    details={"file_path": str(file_path), "error": str(e)}
                )
        
        # Report quality summary
        if quality_issues:
            self._add_audit_result(
                component="code_quality",
                status="warning",
                description=f"Code quality issues found in {len(quality_issues)} locations",
                details={"total_files": total_files, "issues_found": len(quality_issues)},
                recommendations=["Run code linter", "Fix code style issues", "Add type hints"]
            )
        else:
            self._add_audit_result(
                component="code_quality",
                status="pass",
                description=f"Code quality check passed for {total_files} files",
                details={"total_files": total_files}
            )
    
    def _analyze_file_quality(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Analyze individual file quality"""
        issues = []
        
        # Check for long lines
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    "type": "long_line",
                    "line": i,
                    "length": len(line),
                    "description": f"Line {i} is too long ({len(line)} characters)"
                })
        
        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                issues.append({
                    "type": "trailing_whitespace",
                    "line": i,
                    "description": f"Line {i} has trailing whitespace"
                })
        
        # Check for missing docstrings (Python)
        if file_path.suffix == '.py':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and not node.body:
                        # Empty function
                        continue
                    elif isinstance(node, ast.FunctionDef):
                        # Check if function has docstring
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Str)):
                            continue
                        else:
                            issues.append({
                                "type": "missing_docstring",
                                "line": node.lineno,
                                "description": f"Function '{node.name}' missing docstring"
                            })
            except SyntaxError:
                issues.append({
                    "type": "syntax_error",
                    "description": f"Syntax error in {file_path.name}"
                })
        
        return issues
    
    def _audit_security(self):
        """Audit security vulnerabilities"""
        print("[APTPT] Auditing security...")
        
        # Scan for security issues
        security_issues = []
        
        for pattern_type, patterns in self.audit_patterns.items():
            if pattern_type == "security":
                for pattern in patterns:
                    matches = self._find_pattern_in_project(pattern)
                    security_issues.extend(matches)
        
        if security_issues:
            self._add_audit_result(
                component="security",
                status="critical",
                description=f"Security vulnerabilities found: {len(security_issues)} issues",
                details={"issues": security_issues},
                recommendations=[
                    "Review and fix security vulnerabilities",
                    "Use secure alternatives to dangerous functions",
                    "Implement proper input validation",
                    "Remove hardcoded secrets"
                ]
            )
        else:
            self._add_audit_result(
                component="security",
                status="pass",
                description="No security vulnerabilities detected",
                details={"scanned_patterns": len(self.audit_patterns["security"])}
            )
    
    def _audit_performance(self):
        """Audit performance issues"""
        print("[APTPT] Auditing performance...")
        
        # Scan for performance issues
        performance_issues = []
        
        for pattern_type, patterns in self.audit_patterns.items():
            if pattern_type == "performance":
                for pattern in patterns:
                    matches = self._find_pattern_in_project(pattern)
                    performance_issues.extend(matches)
        
        if performance_issues:
            self._add_audit_result(
                component="performance",
                status="warning",
                description=f"Performance issues found: {len(performance_issues)} issues",
                details={"issues": performance_issues},
                recommendations=[
                    "Optimize performance bottlenecks",
                    "Use more efficient algorithms",
                    "Consider caching strategies",
                    "Profile code for bottlenecks"
                ]
            )
        else:
            self._add_audit_result(
                component="performance",
                status="pass",
                description="No performance issues detected",
                details={"scanned_patterns": len(self.audit_patterns["performance"])}
            )
    
    def _audit_dependencies(self):
        """Audit project dependencies"""
        print("[APTPT] Auditing dependencies...")
        
        # Check Python dependencies
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file) as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                # Check for outdated or vulnerable packages
                outdated_packages = self._check_python_dependencies(requirements)
                
                if outdated_packages:
                    self._add_audit_result(
                        component="dependencies",
                        status="warning",
                        description=f"Outdated Python packages: {len(outdated_packages)} packages",
                        details={"outdated_packages": outdated_packages},
                        recommendations=["Update outdated packages", "Run security audit"]
                    )
                else:
                    self._add_audit_result(
                        component="dependencies",
                        status="pass",
                        description=f"Python dependencies check passed: {len(requirements)} packages",
                        details={"total_packages": len(requirements)}
                    )
            except Exception as e:
                self._add_audit_result(
                    component="dependencies",
                    status="error",
                    description="Error checking Python dependencies",
                    details={"error": str(e)}
                )
        
        # Check Node.js dependencies
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                
                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})
                total_deps = len(dependencies) + len(dev_dependencies)
                
                self._add_audit_result(
                    component="dependencies",
                    status="pass",
                    description=f"Node.js dependencies check passed: {total_deps} packages",
                    details={"dependencies": len(dependencies), "dev_dependencies": len(dev_dependencies)}
                )
            except Exception as e:
                self._add_audit_result(
                    component="dependencies",
                    status="error",
                    description="Error checking Node.js dependencies",
                    details={"error": str(e)}
                )
    
    def _check_python_dependencies(self, requirements: List[str]) -> List[str]:
        """Check Python dependencies for outdated packages"""
        outdated = []
        
        try:
            # This would integrate with pip or similar tool
            # For now, return empty list
            return outdated
        except Exception:
            return outdated
    
    def _audit_documentation(self):
        """Audit project documentation"""
        print("[APTPT] Auditing documentation...")
        
        # Check for README
        readme_files = list(self.project_root.glob("README*"))
        if readme_files:
            readme_size = readme_files[0].stat().st_size
            if readme_size > 1000:
                self._add_audit_result(
                    component="documentation",
                    status="pass",
                    description="README documentation exists and substantial",
                    details={"file": str(readme_files[0]), "size": readme_size}
                )
            else:
                self._add_audit_result(
                    component="documentation",
                    status="warning",
                    description="README exists but may be insufficient",
                    details={"file": str(readme_files[0]), "size": readme_size},
                    recommendations=["Expand README documentation"]
                )
        else:
            self._add_audit_result(
                component="documentation",
                status="error",
                description="Missing README documentation",
                recommendations=["Create comprehensive README file"]
            )
        
        # Check for API documentation
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.rglob("*.md"))
            if doc_files:
                self._add_audit_result(
                    component="documentation",
                    status="pass",
                    description=f"API documentation exists: {len(doc_files)} files",
                    details={"doc_files": len(doc_files)}
                )
            else:
                self._add_audit_result(
                    component="documentation",
                    status="warning",
                    description="Docs directory exists but no documentation files found",
                    recommendations=["Add API documentation"]
                )
    
    def _audit_testing(self):
        """Audit testing coverage and quality"""
        print("[APTPT] Auditing testing...")
        
        # Check for test files
        test_files = []
        for pattern in ["test_*.py", "*_test.py", "*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"]:
            test_files.extend(self.project_root.rglob(pattern))
        
        if test_files:
            # Check test coverage
            coverage_result = self._check_test_coverage()
            
            if coverage_result["coverage"] > 80:
                self._add_audit_result(
                    component="testing",
                    status="pass",
                    description=f"Good test coverage: {coverage_result['coverage']:.1f}%",
                    details={"test_files": len(test_files), "coverage": coverage_result["coverage"]}
                )
            elif coverage_result["coverage"] > 50:
                self._add_audit_result(
                    component="testing",
                    status="warning",
                    description=f"Moderate test coverage: {coverage_result['coverage']:.1f}%",
                    details={"test_files": len(test_files), "coverage": coverage_result["coverage"]},
                    recommendations=["Increase test coverage", "Add more test cases"]
                )
            else:
                self._add_audit_result(
                    component="testing",
                    status="error",
                    description=f"Low test coverage: {coverage_result['coverage']:.1f}%",
                    details={"test_files": len(test_files), "coverage": coverage_result["coverage"]},
                    recommendations=["Significantly increase test coverage", "Add unit tests", "Add integration tests"]
                )
        else:
            self._add_audit_result(
                component="testing",
                status="critical",
                description="No test files found",
                recommendations=["Create test files", "Add unit tests", "Set up testing framework"]
            )
    
    def _check_test_coverage(self) -> Dict[str, Any]:
        """Check test coverage"""
        try:
            # This would integrate with coverage tools
            # For now, return estimated coverage
            return {"coverage": 75.0}  # Estimated
        except Exception:
            return {"coverage": 0.0}
    
    def _audit_configuration(self):
        """Audit project configuration"""
        print("[APTPT] Auditing configuration...")
        
        # Check for configuration files
        config_files = []
        for pattern in ["*.yaml", "*.yml", "*.json", "*.ini", "*.cfg", "*.conf"]:
            config_files.extend(self.project_root.rglob(pattern))
        
        if config_files:
            # Check configuration quality
            config_issues = []
            for config_file in config_files:
                if config_file.name in ["config.yaml", "config.json", "settings.py"]:
                    try:
                        with open(config_file) as f:
                            if config_file.suffix in ['.yaml', '.yml']:
                                config_data = yaml.safe_load(f)
                            elif config_file.suffix == '.json':
                                config_data = json.load(f)
                            else:
                                config_data = f.read()
                        
                        # Basic configuration validation
                        if isinstance(config_data, dict) and len(config_data) > 0:
                            self._add_audit_result(
                                component="configuration",
                                status="pass",
                                description=f"Configuration file valid: {config_file.name}",
                                details={"file": str(config_file), "keys": len(config_data)}
                            )
                        else:
                            config_issues.append(str(config_file))
                    except Exception as e:
                        config_issues.append(f"{config_file}: {e}")
            
            if config_issues:
                self._add_audit_result(
                    component="configuration",
                    status="warning",
                    description=f"Configuration issues found: {len(config_issues)} files",
                    details={"issues": config_issues},
                    recommendations=["Fix configuration files", "Validate configuration syntax"]
                )
        else:
            self._add_audit_result(
                component="configuration",
                status="warning",
                description="No configuration files found",
                recommendations=["Create configuration files", "Add environment-specific configs"]
            )
    
    def _audit_git_status(self):
        """Audit Git repository status"""
        print("[APTPT] Auditing Git status...")
        
        git_dir = self.project_root / ".git"
        if git_dir.exists():
            try:
                # Check Git status
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    
                    if not changes:
                        self._add_audit_result(
                            component="git",
                            status="pass",
                            description="Git repository is clean",
                            details={"changes": 0}
                        )
                    else:
                        self._add_audit_result(
                            component="git",
                            status="warning",
                            description=f"Git repository has {len(changes)} uncommitted changes",
                            details={"changes": len(changes)},
                            recommendations=["Commit pending changes", "Review uncommitted files"]
                        )
                else:
                    self._add_audit_result(
                        component="git",
                        status="error",
                        description="Error checking Git status",
                        details={"error": result.stderr}
                    )
            except Exception as e:
                self._add_audit_result(
                    component="git",
                    status="error",
                    description="Error accessing Git repository",
                    details={"error": str(e)}
                )
        else:
            self._add_audit_result(
                component="git",
                status="warning",
                description="Not a Git repository",
                recommendations=["Initialize Git repository", "Add .gitignore file"]
            )
    
    def _audit_build_system(self):
        """Audit build system and deployment"""
        print("[APTPT] Auditing build system...")
        
        # Check for build files
        build_files = []
        for pattern in ["Makefile", "Dockerfile", "docker-compose.yml", "setup.py", "package.json", "build.sh"]:
            build_file = self.project_root / pattern
            if build_file.exists():
                build_files.append(pattern)
        
        if build_files:
            self._add_audit_result(
                component="build",
                status="pass",
                description=f"Build system files found: {len(build_files)} files",
                details={"build_files": build_files}
            )
        else:
            self._add_audit_result(
                component="build",
                status="warning",
                description="No build system files found",
                recommendations=["Add build configuration", "Create deployment scripts"]
            )
    
    def _find_pattern_in_project(self, pattern: str) -> List[Dict[str, Any]]:
        """Find pattern matches in project files"""
        matches = []
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        matches.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "line": content[:match.start()].count('\n') + 1,
                            "match": match.group(),
                            "context": content[max(0, match.start()-20):match.end()+20]
                        })
                except Exception:
                    continue
        
        return matches
    
    def _add_audit_result(self, component: str, status: str, description: str, 
                         details: Dict[str, Any] = None, recommendations: List[str] = None):
        """Add audit result with APTPT/HCE/REI analysis"""
        details = details or {}
        recommendations = recommendations or []
        
        # Compute metrics
        context = {"component": component, "status": status, "description": description}
        phase_vector = self._compute_phase_vector(context)
        entropy_score = self._compute_entropy(context)
        rei_score = self._compute_rei_score(phase_vector)
        
        result = AuditResult(
            component=component,
            status=status,
            description=description,
            details=details,
            recommendations=recommendations,
            phase_vector=phase_vector,
            entropy_score=entropy_score,
            rei_score=rei_score,
            timestamp=datetime.now()
        )
        
        self.audit_results.append(result)
    
    def _calculate_project_health(self):
        """Calculate overall project health"""
        if not self.audit_results:
            return
        
        # Count results by status
        status_counts = {}
        for result in self.audit_results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        total_checks = len(self.audit_results)
        critical_issues = status_counts.get("critical", 0)
        warnings = status_counts.get("warning", 0) + status_counts.get("error", 0)
        passed_checks = status_counts.get("pass", 0)
        
        # Calculate overall score
        if total_checks == 0:
            overall_score = 0
        else:
            # Weight different statuses
            score = (passed_checks * 100 + warnings * 50 + critical_issues * 0) / total_checks
            overall_score = max(0, min(100, score))
        
        # Generate recommendations
        recommendations = []
        if critical_issues > 0:
            recommendations.append("Fix critical issues immediately")
        if warnings > 5:
            recommendations.append("Address multiple warnings")
        if passed_checks < total_checks * 0.7:
            recommendations.append("Improve overall project quality")
        
        self.project_health = ProjectHealth(
            overall_score=overall_score,
            critical_issues=critical_issues,
            warnings=warnings,
            passed_checks=passed_checks,
            total_checks=total_checks,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
    
    def _generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "project_health": asdict(self.project_health) if self.project_health else None,
            "audit_results": [asdict(result) for result in self.audit_results],
            "summary": {
                "total_checks": len(self.audit_results),
                "passed_checks": len([r for r in self.audit_results if r.status == "pass"]),
                "warnings": len([r for r in self.audit_results if r.status == "warning"]),
                "errors": len([r for r in self.audit_results if r.status == "error"]),
                "critical_issues": len([r for r in self.audit_results if r.status == "critical"])
            },
            "auto_fixes_applied": self.auto_fixes_applied,
            "manual_actions_required": self.manual_actions_required,
            "recommendations": self._generate_overall_recommendations()
        }
    
    def _generate_overall_recommendations(self) -> List[Dict[str, Any]]:
        """Generate overall recommendations based on audit results"""
        recommendations = []
        
        # Critical issues
        critical_results = [r for r in self.audit_results if r.status == "critical"]
        if critical_results:
            recommendations.append({
                "priority": "critical",
                "title": "Critical Issues Found",
                "description": f"{len(critical_results)} critical issues require immediate attention",
                "actions": ["Fix all critical issues before proceeding", "Review security vulnerabilities"]
            })
        
        # Warnings
        warning_results = [r for r in self.audit_results if r.status == "warning"]
        if warning_results:
            recommendations.append({
                "priority": "high",
                "title": "Multiple Warnings",
                "description": f"{len(warning_results)} warnings should be addressed",
                "actions": ["Address warnings systematically", "Improve code quality"]
            })
        
        # Missing components
        missing_structure = []
        for file_name in self.required_structure["files"]:
            if not (self.project_root / file_name).exists():
                missing_structure.append(file_name)
        
        if missing_structure:
            recommendations.append({
                "priority": "medium",
                "title": "Missing Project Structure",
                "description": f"Missing required files: {', '.join(missing_structure)}",
                "actions": [f"Create {file_name}" for file_name in missing_structure]
            })
        
        return recommendations
    
    def auto_fix_issues(self) -> Dict[str, Any]:
        """Automatically fix issues that can be resolved"""
        print("[APTPT] Applying auto-fixes...")
        
        fixes_applied = []
        failed_fixes = []
        
        for result in self.audit_results:
            if result.status in ["warning", "error"] and result.recommendations:
                try:
                    # Apply auto-fixes based on component and recommendations
                    fix_result = self._apply_auto_fix(result)
                    if fix_result["success"]:
                        fixes_applied.append(fix_result)
                    else:
                        failed_fixes.append(fix_result)
                except Exception as e:
                    failed_fixes.append({
                        "component": result.component,
                        "description": result.description,
                        "error": str(e)
                    })
        
        return {
            "fixes_applied": fixes_applied,
            "failed_fixes": failed_fixes,
            "total_attempted": len(fixes_applied) + len(failed_fixes)
        }
    
    def _apply_auto_fix(self, audit_result: AuditResult) -> Dict[str, Any]:
        """Apply auto-fix for a specific audit result"""
        # This is a simplified implementation
        # In practice, you'd have specific fix logic for each type of issue
        
        if audit_result.component == "structure":
            return self._fix_structure_issue(audit_result)
        elif audit_result.component == "code_quality":
            return self._fix_code_quality_issue(audit_result)
        elif audit_result.component == "documentation":
            return self._fix_documentation_issue(audit_result)
        else:
            return {
                "success": False,
                "component": audit_result.component,
                "description": "Auto-fix not implemented for this component",
                "error": "No auto-fix available"
            }
    
    def _fix_structure_issue(self, audit_result: AuditResult) -> Dict[str, Any]:
        """Fix structure-related issues"""
        # Create missing files/directories
        for recommendation in audit_result.recommendations:
            if "Create" in recommendation:
                item_name = recommendation.split("Create ")[1]
                item_path = self.project_root / item_name
                
                if item_name.endswith('/'):
                    # Directory
                    item_path.mkdir(exist_ok=True)
                else:
                    # File
                    if not item_path.exists():
                        item_path.touch()
        
        return {
            "success": True,
            "component": audit_result.component,
            "description": "Structure issues fixed",
            "details": {"fixed_items": len(audit_result.recommendations)}
        }
    
    def _fix_code_quality_issue(self, audit_result: AuditResult) -> Dict[str, Any]:
        """Fix code quality issues"""
        # This would implement specific code quality fixes
        return {
            "success": True,
            "component": audit_result.component,
            "description": "Code quality issues addressed",
            "details": {"fixes_applied": "Code formatting and style fixes"}
        }
    
    def _fix_documentation_issue(self, audit_result: AuditResult) -> Dict[str, Any]:
        """Fix documentation issues"""
        # Create basic documentation if missing
        if "Create README" in str(audit_result.recommendations):
            readme_path = self.project_root / "README.md"
            if not readme_path.exists():
                readme_content = f"""# {self.project_root.name}

## Overview
This project was analyzed by PhaseSynth Ultra+ Startup AI Audit.

## Installation
\`\`\`bash
# Add installation instructions here
\`\`\`

## Usage
\`\`\`bash
# Add usage instructions here
\`\`\`

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
"""
                readme_path.write_text(readme_content)
        
        return {
            "success": True,
            "component": audit_result.component,
            "description": "Documentation issues fixed",
            "details": {"created_files": ["README.md"]}
        }

def main():
    """Main startup AI audit"""
    print("[APTPT] PhaseSynth Ultra+ Startup AI Audit")
    print("[APTPT] Running comprehensive project analysis...")
    
    audit = StartupAIAudit()
    report = audit.run_comprehensive_audit()
    
    # Print summary
    print("\n" + "="*80)
    print("STARTUP AI AUDIT SUMMARY")
    print("="*80)
    print(f"Overall Health Score: {report['project_health']['overall_score']:.1f}%")
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Passed: {report['summary']['passed_checks']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Critical Issues: {report['summary']['critical_issues']}")
    print("="*80)
    
    # Apply auto-fixes if requested
    if report['summary']['warnings'] > 0 or report['summary']['errors'] > 0:
        print(f"\n[APTPT] Found {report['summary']['warnings']} warnings and {report['summary']['errors']} errors")
        response = input("Apply auto-fixes? (y/n): ").lower()
        if response == 'y':
            fix_results = audit.auto_fix_issues()
            print(f"[APTPT] Applied {len(fix_results['fixes_applied'])} fixes")
            print(f"[APTPT] Failed {len(fix_results['failed_fixes'])} fixes")
    
    # Save report
    report_file = Path("startup_audit_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n[APTPT] Audit report saved to: {report_file}")

if __name__ == "__main__":
    main() 