import re
import ast
import math

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*=\s*[\'"][A-Za-z0-9_\-\.]{16,}[\'"]',
     "Hardcoded Secret / API Key", "high", "security", "Potential hardcoded API token or credential detected. Move credentials to environment variables."),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID", "critical", "security", "AWS Access Key ID exposed directly in code."),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Personal Access Token", "critical", "security", "Exposed GitHub Personal Access Token."),
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Hardcoded Private Key", "critical", "security", "Cryptographic private key detected in source code."),
    (r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', "JWT Token", "medium", "security", "Possible hardcoded JWT token found."),
    (r'(?i)postgres(?:ql)?://[a-zA-Z0-9_\-]+:[^@\s]+@[a-zA-Z0-9_\.\-]+(?::\d+)?/[a-zA-Z0-9_\-]+', "Database Connection String with Password", "critical", "security", "Database credentials with password committed in plain text."),
    (r'(?i)(password|passwd|pwd)\s*=\s*[\'"][^\'"]{4,}[\'"]', "Hardcoded Password", "high", "security", "Hardcoded password found in variable assignment.")
]

GENERIC_SECURITY_PATTERNS = [
    (r'(?i)f["\'].*(?:SELECT|INSERT|UPDATE|DELETE)\s+.*\{.+\}',
     "SQL Injection via f-string Interpolation", "critical", "security", "Dynamic SQL query formed with Python f-string interpolation. Attackers can execute arbitrary SQL commands. Use parameterized queries (e.g. cursor.execute('... WHERE user = ?', (username,)))."),
    (r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*\s+(FROM|INTO|WHERE)\s+.*(\+|%|\.format|\.|\$)',
     "SQL Injection via String Concatenation", "critical", "security", "Dynamic SQL query formed with string interpolation or concatenation. Use parameterized queries or prepared statements."),
    (r'(?i)(?:\$)?(password|passwd|pwd|pass|db_pass)\s*=\s*[\'"][^\'"]{4,}[\'"]',
     "Hardcoded Credentials / Password", "critical", "security", "Hardcoded password or credential discovered in source code. Move sensitive credentials to environment variables or a secret vault."),
    (r'\beval\s*\(', "Dangerous eval() Execution", "critical", "security", "eval() allows execution of arbitrary code, creating severe Remote Code Execution (RCE) vectors."),
    (r'\bexec\s*\(', "Dangerous exec() Execution", "high", "security", "exec() dynamically evaluates arbitrary statements. Avoid dynamic execution of unverified inputs."),
    (r'dangerouslySetInnerHTML', "Dangerous React innerHTML", "high", "security", "dangerouslySetInnerHTML exposes the component to Cross-Site Scripting (XSS). Sanitize HTML using DOMPurify."),
    (r'\.innerHTML\s*(\+?=|=)', "Direct innerHTML Assignment (XSS)", "high", "security", "Direct innerHTML assignment bypasses HTML escaping and can lead to XSS attacks. Use textContent or safe sanitization."),
    (r'shell\s*=\s*True', "subprocess with shell=True", "critical", "security", "Executing subprocess with shell=True is vulnerable to command injection if input contains shell metacharacters."),
    (r'(?i)hashlib\.md5\(', "Cryptographically Weak Hash (MD5)", "high", "security", "MD5 is cryptographically broken and vulnerable to collision attacks. Use SHA-256 or bcrypt/argon2 for passwords."),
    (r'(?i)hashlib\.sha1\(', "Cryptographically Weak Hash (SHA1)", "high", "security", "SHA-1 is deprecated for security purposes due to known collision vulnerabilities. Use SHA-256.")
]

PERFORMANCE_PATTERNS = [
    (r'for\s+.*in\s+.*:\s*\n(?:\s+.*)*for\s+.*in\s+.*:',
     "Nested Loops (Potential O(N^2) Complexity)", "medium", "performance", "Nested iterations detected. For large datasets, this can lead to quadratic time complexity. Consider hash maps or set lookups."),
    (r'(?i)\.addEventListener\([^)]+\)(?![\s\S]*\.removeEventListener)',
     "Event Listener Memory Leak Risk", "medium", "performance", "Event listener added without corresponding teardown or cleanup logic in component lifecycle."),
    (r'time\.sleep\s*\(', "Synchronous Thread Blocking Sleep", "low", "performance", "Synchronous sleep blocks the active thread. In asynchronous code, use asyncio.sleep() instead.")
]

def strip_comments(code: str, language: str = "go") -> str:
    """Removes comments so keyword searches aren't fooled by words in comments."""
    lang = (language or "").lower()
    if lang in ("go", "javascript", "typescript", "c", "cpp", "java", "php", "csharp"):
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    elif lang in ("python", "py", "ruby", "bash", "sh"):
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    return code

# Go-specific checks
def check_go_rules(code: str, lines: list) -> list:
    issues = []
    clean_code = strip_comments(code, "go")
    clean_lines = clean_code.splitlines()

    has_go_routine = any(re.search(r'\bgo\s+(func|\w+)', line) for line in clean_lines)
    
    # Check for shared maps: var name = make(map[...]) or name := make(map[...])
    map_vars = []
    for line in clean_lines:
        m = re.search(r'(?:var\s+(\w+)\s*=\s*make\s*\(\s*map|(\w+)\s*:=\s*make\s*\(\s*map)', line)
        if m:
            map_vars.append(m.group(1) or m.group(2))

    has_mutex = any("sync.Mutex" in line or "sync.RWMutex" in line for line in clean_lines)

    # 1. Concurrency Data Race on Map
    if has_go_routine and map_vars and not has_mutex:
        for map_name in map_vars:
            # Find the goroutine where this map is used
            in_goroutine = False
            goroutine_start = 1
            for idx, line in enumerate(lines, 1):
                clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
                if re.search(r'\bgo\s+func', clean_l):
                    in_goroutine = True
                    goroutine_start = idx
                if in_goroutine and f"{map_name}[" in clean_l:
                    issues.append({
                        "id": f"go-race-{len(issues)+1}",
                        "line_start": idx,
                        "line_end": idx,
                        "category": "bug",
                        "severity": "critical",
                        "title": f"Data Race: Unsynchronized Map Write to '{map_name}' in Goroutine",
                        "description": f"Go built-in maps are not safe for concurrent access. Goroutine modifies '{map_name}' without synchronization primitives (sync.Mutex or sync.RWMutex). Under concurrent requests, this will trigger a fatal runtime crash: 'fatal error: concurrent map read and map write'.",
                        "impact": "Fatal process termination (SIGSEGV/panic) and service crash under concurrent load.",
                        "suggestion": f"Wrap '{map_name}' with a sync.RWMutex (call mu.Lock()/Unlock() around writes and mu.RLock()/RUnlock() around reads), or migrate to sync.Map.",
                        "original_code": line.strip(),
                        "fixed_code": f"sessionMu.Lock()\n{line.strip()}\nsessionMu.Unlock()"
                    })
                    break
                if in_goroutine and "}" in clean_l:
                    in_goroutine = False

            # Also check for unsynchronized reads of the map outside the goroutine
            for idx, line in enumerate(lines, 1):
                clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
                if f"{map_name}[" in clean_l and "=" in clean_l and not re.search(r'\bgo\s+', clean_l):
                    # Check if it's a read (LHS := map[RHS] or val = map[RHS])
                    if re.search(rf':=\s*{map_name}\[', clean_l) or re.search(rf'=\s*{map_name}\[', clean_l):
                        issues.append({
                            "id": f"go-race-read-{len(issues)+1}",
                            "line_start": idx,
                            "line_end": idx,
                            "category": "bug",
                            "severity": "critical",
                            "title": f"Data Race: Unsynchronized Map Read of '{map_name}' Concurrent with Goroutines",
                            "description": f"Reading from '{map_name}' while a background goroutine may concurrently write to it causes a data race in Go runtime.",
                            "impact": "Memory corruption or immediate panic during concurrent HTTP handler execution.",
                            "suggestion": f"Acquire a read lock using sync.RWMutex (e.g. sessionMu.RLock() / defer sessionMu.RUnlock()) before reading '{map_name}'.",
                            "original_code": line.strip(),
                            "fixed_code": f"sessionMu.RLock()\n{line.strip()}\nsessionMu.RUnlock()"
                        })
                        break

    # 2. Check for http.ListenAndServe without timeouts
    for idx, line in enumerate(lines, 1):
        clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
        if re.search(r'http\.ListenAndServe\s*\(', clean_l):
            issues.append({
                "id": f"go-srv-{len(issues)+1}",
                "line_start": idx,
                "line_end": idx,
                "category": "security",
                "severity": "medium",
                "title": "Default HTTP Server Without Read/Write Timeouts",
                "description": "Using http.ListenAndServe with default timeouts exposes the server to connection starvation and Slowloris Denial of Service (DoS) attacks.",
                "impact": "Unbounded client connections can exhaust file descriptors and system resources.",
                "suggestion": "Instantiate &http.Server with explicit ReadHeaderTimeout, ReadTimeout, and WriteTimeout.",
                "original_code": line.strip(),
                "fixed_code": "srv := &http.Server{\n    Addr: \":8080\",\n    ReadTimeout: 10 * time.Second,\n    WriteTimeout: 10 * time.Second,\n}\nsrv.ListenAndServe()"
            })

    return issues

# PHP-specific checks
def check_php_rules(code: str, lines: list) -> list:
    issues = []
    clean_code = strip_comments(code, "php")
    clean_lines = clean_code.splitlines()

    for idx, line in enumerate(lines, 1):
        clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
        # SQL Injection with $_GET / $_POST
        if re.search(r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*\.\s*\$_(GET|POST|REQUEST)', clean_l) or \
           re.search(r'\$sql\s*=\s*.*(\.\s*\$|LIKE\s*\'%\"\s*\.\s*\$)', clean_l):
            issues.append({
                "id": f"php-sql-{len(issues)+1}",
                "line_start": idx,
                "line_end": idx,
                "category": "security",
                "severity": "critical",
                "title": "SQL Injection via Concatenated Query",
                "description": "SQL statement is directly concatenating unsanitized user inputs. Attackers can manipulate queries to bypass authentication or extract entire database records.",
                "impact": "Full database compromise, unauthorized data exfiltration, or data deletion.",
                "suggestion": "Use prepared statements with PDO or mysqli ($stmt = $conn->prepare(...); $stmt->bind_param(...)).",
                "original_code": line.strip(),
                "fixed_code": "$stmt = $conn->prepare('SELECT id, title FROM products WHERE category_id = ?');\n$stmt->bind_param('i', $cat_id);\n$stmt->execute();"
            })
        # Reflected XSS
        if re.search(r'echo\s+.*\$_(GET|POST|REQUEST)\[', clean_l) or re.search(r'echo\s+[\'"]<[^>]+>\s*\.\s*\$', clean_l):
            issues.append({
                "id": f"php-xss-{len(issues)+1}",
                "line_start": idx,
                "line_end": idx,
                "category": "security",
                "severity": "high",
                "title": "Reflected Cross-Site Scripting (XSS)",
                "description": "User-supplied query parameters are printed directly into HTML without escaping.",
                "impact": "Execution of arbitrary JavaScript in the victim's browser, enabling session hijacking and cookie theft.",
                "suggestion": "Escape all dynamic HTML output using htmlspecialchars($str, ENT_QUOTES, 'UTF-8').",
                "original_code": line.strip(),
                "fixed_code": "echo htmlspecialchars($search_keyword, ENT_QUOTES, 'UTF-8');"
            })
    return issues

# JavaScript / TypeScript-specific checks
def check_js_rules(code: str, lines: list) -> list:
    issues = []
    clean_code = strip_comments(code, "js")
    clean_lines = clean_code.splitlines()

    has_set_interval = any("setInterval" in line for line in clean_lines)
    has_unbounded_push = any(re.search(r'\.push\(', line) for line in clean_lines)
    if has_set_interval and has_unbounded_push:
        for idx, line in enumerate(lines, 1):
            clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
            if "setInterval" in clean_l:
                issues.append({
                    "id": f"js-leak-{len(issues)+1}",
                    "line_start": idx,
                    "line_end": min(idx + 10, len(lines)),
                    "category": "performance",
                    "severity": "high",
                    "title": "Unbounded Memory Accumulation in Timer",
                    "description": "Objects or arrays are continuously pushed into memory inside an active setInterval without an eviction policy or cleanup.",
                    "impact": "Browser tab or Node process memory steadily increases until Out-Of-Memory (OOM) crash.",
                    "suggestion": "Implement a bounded circular buffer (e.g. ring buffer or FIFO eviction) and store timer ID for clearInterval() cleanup.",
                    "original_code": line.strip(),
                    "fixed_code": "if (this.cache.length > 100) this.cache.shift();\nthis.cache.push(item);"
                })
                break

    for idx, line in enumerate(lines, 1):
        clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
        if re.search(r'\bdocument\.write\s*\(', clean_l):
            issues.append({
                "id": f"js-docwrite-{len(issues)+1}",
                "line_start": idx,
                "line_end": idx,
                "category": "security",
                "severity": "high",
                "title": "Use of document.write()",
                "description": "document.write() is an outdated API prone to XSS attacks and poor rendering performance.",
                "impact": "Security vulnerability and forced document re-parsing.",
                "suggestion": "Use textContent or safe DOM node manipulation.",
                "original_code": line.strip(),
                "fixed_code": "container.textContent = safeText;"
            })
        if re.search(r'[^\!=]==[^=]', clean_l):
            issues.append({
                "id": f"js-eq-{len(issues)+1}",
                "line_start": idx,
                "line_end": idx,
                "category": "maintainability",
                "severity": "low",
                "title": "Loose Equality '==' Used",
                "description": "Loose equality '==' performs implicit type coercion which can trigger unexpected bugs (e.g. '' == 0 is true).",
                "impact": "Subtle logic errors and type confusion bugs.",
                "suggestion": "Always use strict equality '===' and '!=='.",
                "original_code": line.strip(),
                "fixed_code": line.strip().replace("==", "===")
            })

    return issues

# C / C++ checks
def check_c_rules(code: str, lines: list) -> list:
    issues = []
    clean_code = strip_comments(code, "c")
    clean_lines = clean_code.splitlines()

    unsafe_funcs = [("strcpy", "critical"), ("strcat", "critical"), ("gets", "critical"), ("sprintf", "high")]
    for func, sev in unsafe_funcs:
        for idx, line in enumerate(lines, 1):
            clean_l = clean_lines[idx - 1] if idx - 1 < len(clean_lines) else ""
            if re.search(rf'\b{func}\s*\(', clean_l):
                issues.append({
                    "id": f"c-buf-{len(issues)+1}",
                    "line_start": idx,
                    "line_end": idx,
                    "category": "security",
                    "severity": sev,
                    "title": f"Unbounded Buffer Copy ({func})",
                    "description": f"Function '{func}()' does not check buffer boundary limits, leading to potential buffer overflow and memory corruption vulnerabilities.",
                    "impact": "Arbitrary code execution, stack smashing, or denial of service.",
                    "suggestion": f"Use safer bounded alternatives like strncpy_s, snprintf, or std::string in C++.",
                    "original_code": line.strip(),
                    "fixed_code": f"snprintf(dest, sizeof(dest), \"%s\", src);"
                })
    return issues

def analyze_code_metrics(code: str, language: str = "python") -> dict:
    lines = code.splitlines()
    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    
    comment_pattern = r'^\s*(#|//|/\*|\*)'
    comment_lines = sum(1 for line in lines if re.match(comment_pattern, line))
    code_lines = total_lines - blank_lines - comment_lines
    
    branch_keywords = [
        r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
        r'\bcase\b', r'\bcatch\b', r'\bexcept\b', r'\b&&|\band\b', r'\|\||\bor\b',
        r'\?'
    ]
    complexity = 1
    for kw in branch_keywords:
        complexity += len(re.findall(kw, code))
        
    if code_lines > 0:
        mi = 171 - 5.2 * math.log(max(1, complexity)) - 0.23 * math.log(max(1, code_lines)) + 16.2 * math.log(max(1, comment_lines + 1))
        maintainability_index = max(0, min(100, int(mi)))
    else:
        maintainability_index = 100

    return {
        "total_lines": total_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "cyclomatic_complexity": complexity,
        "maintainability_index": maintainability_index,
        "complexity_rating": "Low" if complexity <= 10 else ("Medium" if complexity <= 25 else "High")
    }

def run_static_checks(code: str, language: str = "python") -> list:
    issues = []
    lines = code.splitlines()
    lang = (language or "").lower()
    
    # 1. Global Regex Checks (Secrets, General Security, Performance)
    all_rules = SECRET_PATTERNS + GENERIC_SECURITY_PATTERNS + PERFORMANCE_PATTERNS
    for pattern, title, severity, category, description in all_rules:
        for idx, line in enumerate(lines, 1):
            if re.search(pattern, line):
                issues.append({
                    "id": f"static-{len(issues)+1}",
                    "line_start": idx,
                    "line_end": idx,
                    "category": category,
                    "severity": severity,
                    "title": title,
                    "description": description,
                    "impact": "Violates best practices and security standards.",
                    "suggestion": "Refactor or eliminate this pattern according to security guidelines.",
                    "original_code": line.strip(),
                    "fixed_code": "# Refactor to avoid pattern"
                })
                
    # 2. Language-Specific Analyzers
    if lang in ("go", "golang"):
        issues.extend(check_go_rules(code, lines))
    elif lang in ("php",):
        issues.extend(check_php_rules(code, lines))
    elif lang in ("javascript", "typescript", "js", "ts"):
        issues.extend(check_js_rules(code, lines))
    elif lang in ("c", "cpp", "c++"):
        issues.extend(check_c_rules(code, lines))
    elif lang in ("python", "py"):
        # Python-specific AST static checks
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Bare except check
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append({
                        "id": f"static-{len(issues)+1}",
                        "line_start": getattr(node, "lineno", 1),
                        "line_end": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                        "category": "bug",
                        "severity": "medium",
                        "title": "Bare 'except:' Clause",
                        "description": "A bare 'except:' catches all exceptions, including SystemExit and KeyboardInterrupt, hiding critical errors.",
                        "impact": "Can make debugging difficult and prevent graceful termination.",
                        "suggestion": "Catch specific exception types, e.g., 'except Exception as e:'.",
                        "original_code": "except:",
                        "fixed_code": "except Exception as e:"
                    })
                # Mutable default argument check
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in node.args.defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            issues.append({
                                "id": f"static-{len(issues)+1}",
                                "line_start": node.lineno,
                                "line_end": node.lineno,
                                "category": "bug",
                                "severity": "high",
                                "title": "Mutable Default Argument",
                                "description": f"Function '{node.name}' uses a mutable default argument (list/dict/set), which persists across multiple calls.",
                                "impact": "Unexpected shared state between calls leading to elusive bugs.",
                                "suggestion": "Use None as default and initialize the mutable object inside the function body.",
                                "original_code": f"def {node.name}(..., arg=[])",
                                "fixed_code": f"def {node.name}(..., arg=None):\n    if arg is None:\n        arg = []"
                            })
        except SyntaxError as e:
            issues.append({
                "id": f"static-{len(issues)+1}",
                "line_start": e.lineno or 1,
                "line_end": e.lineno or 1,
                "category": "bug",
                "severity": "critical",
                "title": "Syntax Error",
                "description": f"Code contains syntax error: {e.msg}",
                "impact": "Code fails to parse or execute.",
                "suggestion": "Fix syntax error at the indicated line.",
                "original_code": lines[e.lineno - 1].strip() if e.lineno and e.lineno <= len(lines) else "",
                "fixed_code": ""
            })
        except Exception:
            pass

    return issues
