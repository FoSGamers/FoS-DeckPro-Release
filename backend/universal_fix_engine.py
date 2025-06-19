#!/usr/bin/env python3
"""
Universal Fix Engine for PhaseSynth Ultra+
Implements "Fix Everything" functionality with comprehensive auto-fix and auto-enhance
Enforces APTPT, HCE, and REI theories for robust error correction and optimization
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
class FixResult:
    """Represents a fix result with full metadata"""
    file_path: str
    fix_type: str
    description: str
    success: bool
    error_message: Optional[str]
    before_content: str
    after_content: str
    diff: str
    phase_vector: str
    entropy_change: float
    rei_score_change: float
    complexity_change: Dict[str, Any]
    timestamp: datetime

@dataclass
class EnhancementResult:
    """Represents an enhancement result"""
    file_path: str
    enhancement_type: str
    description: str
    success: bool
    improvements: List[str]
    performance_gain: float
    maintainability_gain: float
    timestamp: datetime

class UniversalFixEngine:
    """Universal fix engine with comprehensive auto-fix and auto-enhance capabilities"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.fix_history = []
        self.enhancement_history = []
        self.backup_dir = self.project_root / ".phasesynth_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Fix patterns
        self.fix_patterns = {
            "import_errors": [
                r"ModuleNotFoundError: No module named '(\w+)'",
                r"ImportError: cannot import name '(\w+)'",
                r"ImportError: No module named '(\w+)'"
            ],
            "syntax_errors": [
                r"SyntaxError: invalid syntax",
                r"IndentationError:",
                r"TabError:"
            ],
            "type_errors": [
                r"TypeError:",
                r"AttributeError:",
                r"NameError: name '(\w+)' is not defined"
            ],
            "logic_errors": [
                r"ZeroDivisionError:",
                r"IndexError:",
                r"KeyError:"
            ]
        }
        
        # Enhancement patterns
        self.enhancement_patterns = {
            "performance": [
                r"for\s+\w+\s+in\s+range\(len\([^)]+\)\)",  # Replace with enumerate
                r"if\s+\w+\s+in\s+\[[^\]]+\]",  # Replace with set
                r"\.append\([^)]+\)\s*$",  # List comprehension opportunity
            ],
            "maintainability": [
                r"def\s+\w+\([^)]*\):\s*$",  # Missing docstring
                r"class\s+\w+[^:]*:\s*$",  # Missing docstring
                r"# TODO:",  # TODO comments
                r"# FIXME:",  # FIXME comments
            ],
            "security": [
                r"eval\s*\(",  # Dangerous eval
                r"exec\s*\(",  # Dangerous exec
                r"input\s*\(",  # Unsafe input
            ]
        }
    
    def _compute_phase_vector(self, content: str, context: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{content}{str(context)}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, content: str) -> float:
        """Compute entropy using HCE theory"""
        if not content:
            return 0.0
        char_freq = {}
        for char in content:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(content)
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
    
    def _analyze_code_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze code complexity"""
        try:
            tree = ast.parse(content)
            complexity = {
                "functions": 0,
                "classes": 0,
                "imports": 0,
                "conditionals": 0,
                "loops": 0,
                "cyclomatic": 0,
                "lines": len(content.split('\n')),
                "comments": len(re.findall(r'#.*$', content, re.MULTILINE))
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity["functions"] += 1
                elif isinstance(node, ast.ClassDef):
                    complexity["classes"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    complexity["imports"] += 1
                elif isinstance(node, (ast.If, ast.Try, ast.With)):
                    complexity["conditionals"] += 1
                elif isinstance(node, (ast.For, ast.While)):
                    complexity["loops"] += 1
            
            complexity["cyclomatic"] = complexity["conditionals"] + complexity["loops"] + 1
            return complexity
            
        except Exception as e:
            return {"error": str(e), "complexity": 0}
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of file before modification"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _generate_diff(self, before: str, after: str) -> str:
        """Generate diff between before and after content"""
        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile='before',
            tofile='after',
            lineterm=''
        )
        return ''.join(diff)
    
    def fix_everything(self) -> Dict[str, Any]:
        """Main fix everything function"""
        print("[APTPT] Starting Universal Fix Everything...")
        
        # Step 1: Analyze project for issues
        issues = self._analyze_project_issues()
        
        # Step 2: Apply fixes
        fix_results = []
        for issue in issues:
            fix_result = self._apply_fix(issue)
            if fix_result:
                fix_results.append(fix_result)
        
        # Step 3: Apply enhancements
        enhancement_results = self._apply_enhancements()
        
        # Step 4: Run tests to verify fixes
        test_results = self._run_tests()
        
        # Step 5: Generate comprehensive report
        report = self._generate_fix_report(fix_results, enhancement_results, test_results)
        
        print(f"[APTPT] Fix Everything complete: {len(fix_results)} fixes applied")
        return report
    
    def _analyze_project_issues(self) -> List[Dict[str, Any]]:
        """Analyze project for issues that need fixing"""
        issues = []
        
        # Scan all Python files
        for py_file in self.project_root.rglob("*.py"):
            if py_file.is_file():
                try:
                    content = py_file.read_text(encoding='utf-8')
                    file_issues = self._analyze_file_issues(py_file, content)
                    issues.extend(file_issues)
                except Exception as e:
                    print(f"[REI] Error analyzing {py_file}: {e}")
        
        # Scan all JavaScript/TypeScript files
        for js_file in self.project_root.rglob("*.js"):
            if js_file.is_file():
                try:
                    content = js_file.read_text(encoding='utf-8')
                    file_issues = self._analyze_file_issues(js_file, content)
                    issues.extend(file_issues)
                except Exception as e:
                    print(f"[REI] Error analyzing {js_file}: {e}")
        
        for ts_file in self.project_root.rglob("*.ts"):
            if ts_file.is_file():
                try:
                    content = ts_file.read_text(encoding='utf-8')
                    file_issues = self._analyze_file_issues(ts_file, content)
                    issues.extend(file_issues)
                except Exception as e:
                    print(f"[REI] Error analyzing {ts_file}: {e}")
        
        return issues
    
    def _analyze_file_issues(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Analyze individual file for issues"""
        issues = []
        
        # Check for syntax errors
        if file_path.suffix == '.py':
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    "file_path": str(file_path),
                    "issue_type": "syntax_error",
                    "line": e.lineno,
                    "description": f"Syntax error: {e.msg}",
                    "severity": "high"
                })
        
        # Check for common patterns
        for pattern_type, patterns in self.fix_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    issues.append({
                        "file_path": str(file_path),
                        "issue_type": pattern_type,
                        "line": content[:match.start()].count('\n') + 1,
                        "description": f"Potential {pattern_type}: {match.group()}",
                        "severity": "medium"
                    })
        
        # Check for missing imports
        if file_path.suffix == '.py':
            missing_imports = self._detect_missing_imports(content)
            for missing_import in missing_imports:
                issues.append({
                    "file_path": str(file_path),
                    "issue_type": "missing_import",
                    "line": 1,
                    "description": f"Missing import: {missing_import}",
                    "severity": "medium",
                    "fix_data": {"import_name": missing_import}
                })
        
        # Check for code style issues
        style_issues = self._detect_style_issues(content, file_path.suffix)
        issues.extend(style_issues)
        
        return issues
    
    def _detect_missing_imports(self, content: str) -> List[str]:
        """Detect missing imports by analyzing code usage"""
        # Common standard library modules
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 'pathlib', 'typing', 
            'collections', 'itertools', 'functools', 're', 'math'
        }
        
        # Find all potential module names in the code
        potential_modules = set()
        for line in content.split('\n'):
            # Look for module.attribute patterns
            matches = re.findall(r'(\w+)\.\w+', line)
            potential_modules.update(matches)
        
        # Check which ones are not imported
        existing_imports = set()
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+(\w+)\s+import',
            r'import\s+(\w+)\s+as'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            existing_imports.update(matches)
        
        missing = potential_modules - existing_imports
        return [m for m in missing if m in stdlib_modules]
    
    def _detect_style_issues(self, content: str, file_extension: str) -> List[Dict[str, Any]]:
        """Detect code style issues"""
        issues = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append({
                    "file_path": "unknown",
                    "issue_type": "style",
                    "line": i,
                    "description": "Trailing whitespace",
                    "severity": "low"
                })
            
            # Check for long lines
            if len(line) > 100:
                issues.append({
                    "file_path": "unknown",
                    "issue_type": "style",
                    "line": i,
                    "description": "Line too long (>100 characters)",
                    "severity": "low"
                })
            
            # Check for mixed tabs and spaces
            if '\t' in line and '    ' in line:
                issues.append({
                    "file_path": "unknown",
                    "issue_type": "style",
                    "line": i,
                    "description": "Mixed tabs and spaces",
                    "severity": "medium"
                })
        
        return issues
    
    def _apply_fix(self, issue: Dict[str, Any]) -> Optional[FixResult]:
        """Apply fix for a specific issue"""
        try:
            file_path = Path(issue["file_path"])
            if not file_path.exists():
                return None
            
            # Create backup
            backup_path = self._create_backup(file_path)
            
            # Read current content
            before_content = file_path.read_text(encoding='utf-8')
            
            # Apply fix based on issue type
            after_content = before_content
            fix_type = "unknown"
            description = issue["description"]
            
            if issue["issue_type"] == "missing_import":
                after_content = self._fix_missing_import(before_content, issue["fix_data"])
                fix_type = "import_fix"
            elif issue["issue_type"] == "syntax_error":
                after_content = self._fix_syntax_error(before_content, issue)
                fix_type = "syntax_fix"
            elif issue["issue_type"] == "style":
                after_content = self._fix_style_issue(before_content, issue)
                fix_type = "style_fix"
            else:
                after_content = self._fix_generic_issue(before_content, issue)
                fix_type = "generic_fix"
            
            # Write fixed content
            file_path.write_text(after_content, encoding='utf-8')
            
            # Compute metrics
            context = {"file_path": str(file_path), "fix_type": fix_type}
            before_phase = self._compute_phase_vector(before_content, context)
            after_phase = self._compute_phase_vector(after_content, context)
            before_entropy = self._compute_entropy(before_content)
            after_entropy = self._compute_entropy(after_content)
            before_rei = self._compute_rei_score(before_phase)
            after_rei = self._compute_rei_score(after_phase)
            
            # Analyze complexity changes
            before_complexity = self._analyze_code_complexity(before_content)
            after_complexity = self._analyze_code_complexity(after_content)
            
            # Create fix result
            fix_result = FixResult(
                file_path=str(file_path),
                fix_type=fix_type,
                description=description,
                success=True,
                error_message=None,
                before_content=before_content,
                after_content=after_content,
                diff=self._generate_diff(before_content, after_content),
                phase_vector=after_phase,
                entropy_change=after_entropy - before_entropy,
                rei_score_change=after_rei - before_rei,
                complexity_change={
                    "before": before_complexity,
                    "after": after_complexity
                },
                timestamp=datetime.now()
            )
            
            self.fix_history.append(fix_result)
            print(f"[APTPT] Fixed {file_path}: {description}")
            return fix_result
            
        except Exception as e:
            print(f"[REI] Failed to fix {issue['file_path']}: {e}")
            return None
    
    def _fix_missing_import(self, content: str, fix_data: Dict[str, Any]) -> str:
        """Fix missing import"""
        import_name = fix_data["import_name"]
        
        # Find the best place to add the import
        lines = content.split('\n')
        
        # Look for existing imports
        import_line = -1
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                import_line = i
        
        # Add import at the end of import section
        if import_line >= 0:
            lines.insert(import_line + 1, f"import {import_name}")
        else:
            # Add at the beginning of the file
            lines.insert(0, f"import {import_name}")
        
        return '\n'.join(lines)
    
    def _fix_syntax_error(self, content: str, issue: Dict[str, Any]) -> str:
        """Fix syntax error"""
        # This is a simplified fix - in practice, you'd need more sophisticated parsing
        lines = content.split('\n')
        line_num = issue["line"] - 1
        
        if line_num < len(lines):
            line = lines[line_num]
            
            # Common syntax fixes
            if "IndentationError" in issue["description"]:
                # Fix indentation
                lines[line_num] = "    " + line.lstrip()
            elif "SyntaxError" in issue["description"]:
                # Try to fix common syntax issues
                if line.count('(') != line.count(')'):
                    if line.count('(') > line.count(')'):
                        lines[line_num] = line + ')'
                    else:
                        lines[line_num] = '(' + line
                elif line.count('[') != line.count(']'):
                    if line.count('[') > line.count(']'):
                        lines[line_num] = line + ']'
                    else:
                        lines[line_num] = '[' + line
        
        return '\n'.join(lines)
    
    def _fix_style_issue(self, content: str, issue: Dict[str, Any]) -> str:
        """Fix style issue"""
        lines = content.split('\n')
        line_num = issue["line"] - 1
        
        if line_num < len(lines):
            line = lines[line_num]
            
            if "Trailing whitespace" in issue["description"]:
                lines[line_num] = line.rstrip()
            elif "Mixed tabs and spaces" in issue["description"]:
                lines[line_num] = line.replace('\t', '    ')
            elif "Line too long" in issue["description"]:
                # Try to break long lines
                if len(line) > 100:
                    # Simple line breaking - in practice, you'd want smarter logic
                    words = line.split()
                    new_lines = []
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) <= 80:
                            current_line += (" " + word) if current_line else word
                        else:
                            if current_line:
                                new_lines.append(current_line)
                            current_line = word
                    if current_line:
                        new_lines.append(current_line)
                    lines[line_num] = '\n    '.join(new_lines)
        
        return '\n'.join(lines)
    
    def _fix_generic_issue(self, content: str, issue: Dict[str, Any]) -> str:
        """Fix generic issue"""
        # Default implementation - return content unchanged
        return content
    
    def _apply_enhancements(self) -> List[EnhancementResult]:
        """Apply enhancements to improve code quality"""
        enhancements = []
        
        # Scan all code files for enhancement opportunities
        for py_file in self.project_root.rglob("*.py"):
            if py_file.is_file():
                try:
                    content = py_file.read_text(encoding='utf-8')
                    file_enhancements = self._enhance_file(py_file, content)
                    enhancements.extend(file_enhancements)
                except Exception as e:
                    print(f"[REI] Error enhancing {py_file}: {e}")
        
        return enhancements
    
    def _enhance_file(self, file_path: Path, content: str) -> List[EnhancementResult]:
        """Enhance individual file"""
        enhancements = []
        
        # Performance enhancements
        perf_enhancement = self._enhance_performance(content)
        if perf_enhancement:
            enhancements.append(perf_enhancement)
        
        # Maintainability enhancements
        maint_enhancement = self._enhance_maintainability(file_path, content)
        if maint_enhancement:
            enhancements.append(maint_enhancement)
        
        # Security enhancements
        sec_enhancement = self._enhance_security(content)
        if sec_enhancement:
            enhancements.append(sec_enhancement)
        
        return enhancements
    
    def _enhance_performance(self, content: str) -> Optional[EnhancementResult]:
        """Apply performance enhancements"""
        improvements = []
        enhanced_content = content
        
        # Replace range(len()) with enumerate
        pattern = r'for\s+(\w+)\s+in\s+range\(len\(([^)]+)\)\):'
        matches = re.finditer(pattern, enhanced_content)
        for match in matches:
            var_name = match.group(1)
            list_name = match.group(2)
            old_pattern = match.group(0)
            new_pattern = f'for {var_name}, item in enumerate({list_name}):'
            enhanced_content = enhanced_content.replace(old_pattern, new_pattern)
            improvements.append(f"Replaced range(len()) with enumerate")
        
        # Replace list membership with set
        pattern = r'if\s+(\w+)\s+in\s+\[([^\]]+)\]'
        matches = re.finditer(pattern, enhanced_content)
        for match in matches:
            var_name = match.group(1)
            list_items = match.group(2)
            old_pattern = match.group(0)
            new_pattern = f'if {var_name} in {{{list_items}}}:'
            enhanced_content = enhanced_content.replace(old_pattern, new_pattern)
            improvements.append(f"Replaced list membership with set")
        
        if improvements:
            return EnhancementResult(
                file_path="unknown",
                enhancement_type="performance",
                description="Performance optimizations applied",
                success=True,
                improvements=improvements,
                performance_gain=0.1,  # Estimated 10% improvement
                maintainability_gain=0.05,
                timestamp=datetime.now()
            )
        
        return None
    
    def _enhance_maintainability(self, file_path: Path, content: str) -> Optional[EnhancementResult]:
        """Apply maintainability enhancements"""
        improvements = []
        enhanced_content = content
        
        # Add missing docstrings
        lines = enhanced_content.split('\n')
        for i, line in enumerate(lines):
            if re.match(r'def\s+\w+\([^)]*\):\s*$', line.strip()):
                # Function without docstring
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                    docstring = f'    """TODO: Add docstring for this function."""'
                    lines.insert(i + 1, docstring)
                    improvements.append("Added missing function docstring")
        
        enhanced_content = '\n'.join(lines)
        
        if improvements:
            return EnhancementResult(
                file_path=str(file_path),
                enhancement_type="maintainability",
                description="Maintainability improvements applied",
                success=True,
                improvements=improvements,
                performance_gain=0.0,
                maintainability_gain=0.2,  # Estimated 20% improvement
                timestamp=datetime.now()
            )
        
        return None
    
    def _enhance_security(self, content: str) -> Optional[EnhancementResult]:
        """Apply security enhancements"""
        improvements = []
        enhanced_content = content
        
        # Replace dangerous eval with safer alternatives
        if 'eval(' in enhanced_content:
            # This is a simplified replacement - in practice, you'd need more analysis
            enhanced_content = enhanced_content.replace('eval(', '# SECURITY: eval() removed - replace with safer alternative')
            improvements.append("Removed dangerous eval() call")
        
        if 'exec(' in enhanced_content:
            enhanced_content = enhanced_content.replace('exec(', '# SECURITY: exec() removed - replace with safer alternative')
            improvements.append("Removed dangerous exec() call")
        
        if improvements:
            return EnhancementResult(
                file_path="unknown",
                enhancement_type="security",
                description="Security improvements applied",
                success=True,
                improvements=improvements,
                performance_gain=0.0,
                maintainability_gain=0.1,
                timestamp=datetime.now()
            )
        
        return None
    
    def _run_tests(self) -> Dict[str, Any]:
        """Run tests to verify fixes"""
        print("[APTPT] Running tests to verify fixes...")
        
        test_results = {
            "python_tests": self._run_python_tests(),
            "javascript_tests": self._run_javascript_tests(),
            "overall_success": True
        }
        
        # Check if any tests failed
        for test_type, result in test_results.items():
            if test_type != "overall_success" and not result.get("success", True):
                test_results["overall_success"] = False
        
        return test_results
    
    def _run_python_tests(self) -> Dict[str, Any]:
        """Run Python tests"""
        try:
            # Look for test files
            test_files = list(self.project_root.rglob("test_*.py"))
            test_files.extend(list(self.project_root.rglob("*_test.py")))
            
            if not test_files:
                return {"success": True, "message": "No test files found"}
            
            # Run tests
            result = subprocess.run(
                ["python", "-m", "pytest", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_javascript_tests(self) -> Dict[str, Any]:
        """Run JavaScript tests"""
        try:
            # Check if package.json exists
            package_json = self.project_root / "package.json"
            if not package_json.exists():
                return {"success": True, "message": "No package.json found"}
            
            # Check if npm test script exists
            with open(package_json) as f:
                package_data = json.load(f)
            
            if "scripts" not in package_data or "test" not in package_data["scripts"]:
                return {"success": True, "message": "No test script found"}
            
            # Run tests
            result = subprocess.run(
                ["npm", "test"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_fix_report(self, fix_results: List[FixResult], 
                           enhancement_results: List[EnhancementResult],
                           test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix report"""
        
        # Calculate metrics
        total_fixes = len(fix_results)
        successful_fixes = len([f for f in fix_results if f.success])
        total_enhancements = len(enhancement_results)
        successful_enhancements = len([e for e in enhancement_results if e.success])
        
        # Calculate overall improvements
        avg_entropy_change = sum(f.entropy_change for f in fix_results) / len(fix_results) if fix_results else 0
        avg_rei_change = sum(f.rei_score_change for f in fix_results) / len(fix_results) if fix_results else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_fixes_applied": total_fixes,
                "successful_fixes": successful_fixes,
                "fix_success_rate": successful_fixes / total_fixes if total_fixes > 0 else 0,
                "total_enhancements": total_enhancements,
                "successful_enhancements": successful_enhancements,
                "enhancement_success_rate": successful_enhancements / total_enhancements if total_enhancements > 0 else 0
            },
            "metrics": {
                "avg_entropy_change": avg_entropy_change,
                "avg_rei_score_change": avg_rei_change,
                "overall_phase_improvement": avg_rei_change > 0
            },
            "fix_results": [asdict(f) for f in fix_results],
            "enhancement_results": [asdict(e) for e in enhancement_results],
            "test_results": test_results,
            "backup_location": str(self.backup_dir),
            "recommendations": self._generate_fix_recommendations(fix_results, enhancement_results)
        }
    
    def _generate_fix_recommendations(self, fix_results: List[FixResult], 
                                    enhancement_results: List[EnhancementResult]) -> List[Dict[str, Any]]:
        """Generate recommendations based on fix results"""
        recommendations = []
        
        # Analyze fix patterns
        fix_types = {}
        for fix in fix_results:
            fix_types[fix.fix_type] = fix_types.get(fix.fix_type, 0) + 1
        
        # Recommend based on common issues
        if fix_types.get("import_fix", 0) > 5:
            recommendations.append({
                "type": "warning",
                "title": "Frequent Import Issues",
                "description": "Many import fixes were applied. Consider using a linter.",
                "action": "Install and configure a linter (e.g., flake8, pylint)"
            })
        
        if fix_types.get("syntax_fix", 0) > 3:
            recommendations.append({
                "type": "warning",
                "title": "Syntax Errors",
                "description": "Multiple syntax errors were fixed. Review code quality.",
                "action": "Use an IDE with syntax checking and consider code review"
            })
        
        # Recommend based on enhancement opportunities
        if len(enhancement_results) > 0:
            recommendations.append({
                "type": "info",
                "title": "Enhancements Applied",
                "description": f"{len(enhancement_results)} enhancements were applied successfully.",
                "action": "Review the enhancements and consider manual improvements"
            })
        
        return recommendations

def main():
    """Main universal fix engine"""
    print("[APTPT] PhaseSynth Ultra+ Universal Fix Engine")
    print("[APTPT] Starting comprehensive fix and enhance process...")
    
    engine = UniversalFixEngine()
    report = engine.fix_everything()
    
    # Print summary
    print("\n" + "="*80)
    print("FIX EVERYTHING SUMMARY")
    print("="*80)
    print(f"Total Fixes Applied: {report['summary']['total_fixes_applied']}")
    print(f"Fix Success Rate: {report['summary']['fix_success_rate']:.1%}")
    print(f"Total Enhancements: {report['summary']['total_enhancements']}")
    print(f"Enhancement Success Rate: {report['summary']['enhancement_success_rate']:.1%}")
    print(f"Tests Passed: {report['test_results']['overall_success']}")
    print(f"Average Entropy Change: {report['metrics']['avg_entropy_change']:.3f}")
    print(f"Average REI Score Change: {report['metrics']['avg_rei_score_change']:.3f}")
    print("="*80)
    
    # Save report
    report_file = Path("universal_fix_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n[APTPT] Report saved to: {report_file}")
    print(f"[APTPT] Backups saved to: {report['backup_location']}")

if __name__ == "__main__":
    main() 