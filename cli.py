#!/usr/bin/env python3
"""
CodeLens AI - CLI Code Reviewer & Security Linter
Usage:
    python cli.py --file <path_to_code> [--lang <language>] [--export <markdown|json|html>]
    python cli.py --sample python_security
"""

import sys
import os
import argparse
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.ai_reviewer import review_code
from backend.export_service import export_to_markdown, export_to_json, export_to_html
from backend.server import SAMPLE_CODES

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ANSI Terminal Colors
BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"

def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".php": "php",
        ".go": "go",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".rs": "rust",
        ".sql": "sql",
        ".html": "html",
        ".css": "css"
    }
    return mapping.get(ext, "plaintext")

def print_banner():
    print(f"{CYAN}{BOLD}")
    print("===================================================================")
    print("                [+] CODELENS AI - CODE REVIEWER                    ")
    print("      Security Audit | Performance | Quality | Unit Tests          ")
    print("===================================================================")
    print(f"{RESET}")


def render_cli_review(result: dict, filename: str):
    score = result.get("score", 0)
    grade = result.get("grade", "N/A")
    issues = result.get("issues", [])
    metrics = result.get("metrics", {})
    summary = result.get("summary", "")
    source = result.get("source", "engine")
    
    score_color = GREEN if score >= 80 else (YELLOW if score >= 60 else RED)
    
    print(f"\n{BOLD}Target:{RESET} {filename}")
    print(f"{BOLD}Engine:{RESET} {source.upper()} | {BOLD}Health Score:{RESET} {score_color}{BOLD}{score}/100 (Grade {grade}){RESET}")
    print(f"{BOLD}Summary:{RESET} {summary}\n")
    
    print(f"{BOLD}--- CODE HEALTH METRICS ---{RESET}")
    print(f"  • Security Score:        {metrics.get('security_score', 'N/A')}/100")
    print(f"  • Performance Score:     {metrics.get('performance_score', 'N/A')}/100")
    print(f"  • Maintainability Index: {metrics.get('maintainability_score', 'N/A')}/100")
    print(f"  • Cyclomatic Complexity: {metrics.get('cyclomatic_complexity', 'N/A')} ({metrics.get('complexity_rating', 'N/A')})")
    print(f"  • Total Lines of Code:   {metrics.get('total_lines', 'N/A')}\n")
    
    print(f"{BOLD}--- ISSUES FOUND ({len(issues)}) ---{RESET}")
    if not issues:
        print(f"{GREEN}✔ No issues detected. Clean and solid code!{RESET}\n")
    else:
        for idx, issue in enumerate(issues, 1):
            sev = issue.get("severity", "info").lower()
            if sev == "critical":
                sev_tag = f"{RED}[CRITICAL]{RESET}"
            elif sev == "high":
                sev_tag = f"{RED}[HIGH]{RESET}"
            elif sev == "medium":
                sev_tag = f"{YELLOW}[MEDIUM]{RESET}"
            elif sev == "low":
                sev_tag = f"{BLUE}[LOW]{RESET}"
            else:
                sev_tag = f"{MAGENTA}[INFO]{RESET}"
                
            line_str = f"L{issue.get('line_start')}"
            if issue.get("line_end") and issue.get("line_end") != issue.get("line_start"):
                line_str += f"-L{issue.get('line_end')}"
                
            cat = issue.get("category", "").upper()
            title = issue.get("title", "Issue")
            desc = issue.get("description", "")
            sugg = issue.get("suggestion", "")
            
            print(f" {idx}. {sev_tag} {BOLD}{title}{RESET} ({CYAN}{cat}{RESET} @ {line_str})")
            print(f"    {desc}")
            if sugg:
                print(f"    {GREEN}💡 Fix: {sugg}{RESET}")
            if issue.get("original_code"):
                print(f"    Snippet: {YELLOW}{issue.get('original_code')}{RESET}")
            print()

def main():
    parser = argparse.ArgumentParser(description="CodeLens AI - Automated Code Reviewer & Linter")
    parser.add_argument("-f", "--file", help="Path to code file to review")
    parser.add_argument("-s", "--sample", choices=list(SAMPLE_CODES.keys()), help="Run review on a built-in demo sample")
    parser.add_argument("-l", "--lang", help="Programming language (auto-detected if omitted)")
    parser.add_argument("--key", help="Gemini API Key (optional, defaults to GEMINI_API_KEY env or local engine)")
    parser.add_argument("-o", "--output", help="Save output report to file (e.g. report.md, report.json, report.html)")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit with code 1 if critical issues are found (CI/CD mode)")

    args = parser.parse_args()
    print_banner()

    if not args.file and not args.sample:
        print(f"{YELLOW}No file or sample specified. Try:{RESET}")
        print("  python cli.py --sample python_security")
        print("  python cli.py --file samples/01_python_auth_vulnerability.py")
        print("  python run.py  (to launch the full web app GUI)")
        sys.exit(0)

    code = ""
    language = args.lang or "python"
    filename = ""

    if args.sample:
        sample_data = SAMPLE_CODES[args.sample]
        code = sample_data["code"]
        language = sample_data["language"]
        filename = f"Sample: {sample_data['name']}"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"{RED}Error: File '{args.file}' not found.{RESET}")
            sys.exit(1)
        code = file_path.read_text(encoding="utf-8", errors="replace")
        language = args.lang or detect_language(args.file)
        filename = str(file_path)

    print(f"Analyzing {filename} ({language})...")
    result = review_code(code, language, api_key=args.key)
    render_cli_review(result, filename)

    # Save output if requested
    if args.output:
        out_path = Path(args.output)
        if out_path.suffix.lower() == ".json":
            content = export_to_json(result)
        elif out_path.suffix.lower() in (".html", ".htm"):
            content = export_to_html(result)
        else:
            content = export_to_markdown(result)
            
        out_path.write_text(content, encoding="utf-8")
        print(f"{GREEN}✔ Report saved to: {out_path.resolve()}{RESET}")

    # Check for critical issues in CI/CD mode
    if args.fail_on_critical:
        critical_count = sum(1 for i in result.get("issues", []) if i.get("severity") == "critical")
        if critical_count > 0:
            print(f"{RED}❌ Build check failed: {critical_count} critical issue(s) detected.{RESET}")
            sys.exit(1)

    print(f"{GREEN}✔ Review complete.{RESET}")

if __name__ == "__main__":
    main()
