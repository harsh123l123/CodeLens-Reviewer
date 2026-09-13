import json
import time

def export_to_markdown(review: dict) -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(review.get("created_at", time.time())))
    score = review.get("score", 0)
    grade = review.get("grade", "N/A")
    language = review.get("language", "Code").capitalize()
    summary = review.get("summary", "No summary provided.")
    metrics = review.get("metrics", {})
    issues = review.get("issues", [])
    test_cases = review.get("test_cases", [])
    
    md = []
    md.append(f"# 🛡️ CodeLens AI - Code Review Report")
    md.append(f"**Generated:** `{timestamp}` | **Language:** `{language}` | **Overall Score:** `{score}/100` (Grade: `{grade}`)\n")
    
    md.append("## 📊 Executive Summary")
    md.append(f"{summary}\n")
    
    md.append("## 📈 Code Health Metrics")
    md.append("| Metric | Value | Rating |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| Security Score | {metrics.get('security_score', 'N/A')}/100 | {'🟢 Strong' if metrics.get('security_score', 0)>=80 else ('🟡 Moderate' if metrics.get('security_score', 0)>=60 else '🔴 Needs Work')} |")
    md.append(f"| Performance Score | {metrics.get('performance_score', 'N/A')}/100 | {'🟢 Strong' if metrics.get('performance_score', 0)>=80 else ('🟡 Moderate' if metrics.get('performance_score', 0)>=60 else '🔴 Needs Work')} |")
    md.append(f"| Maintainability Index | {metrics.get('maintainability_score', 'N/A')}/100 | {'🟢 High' if metrics.get('maintainability_score', 0)>=75 else ('🟡 Medium' if metrics.get('maintainability_score', 0)>=50 else '🔴 Low')} |")
    md.append(f"| Cyclomatic Complexity | {metrics.get('cyclomatic_complexity', 'N/A')} | {metrics.get('complexity_rating', metrics.get('estimated_complexity', 'N/A'))} |\n")
    
    md.append("## 🔍 Issues Found")
    if not issues:
        md.append("✅ **No critical or major issues found.** Great job on clean code!")
    else:
        for idx, issue in enumerate(issues, 1):
            severity = issue.get("severity", "info").upper()
            badge = "🔴" if severity == "CRITICAL" else ("🟠" if severity == "HIGH" else ("🟡" if severity == "MEDIUM" else "🔵"))
            category = issue.get("category", "general").title()
            title = issue.get("title", "Untitled Issue")
            lines = f"Lines {issue.get('line_start', '?')}-{issue.get('line_end', '?')}" if issue.get("line_start") != issue.get("line_end") else f"Line {issue.get('line_start', '?')}"
            
            md.append(f"### {idx}. {badge} [{severity}] {title} ({category} - {lines})")
            md.append(f"**Description:** {issue.get('description', '')}\n")
            if issue.get("impact"):
                md.append(f"**Impact:** {issue.get('impact')}\n")
            if issue.get("suggestion"):
                md.append(f"**Recommendation:** {issue.get('suggestion')}\n")
            if issue.get("original_code"):
                md.append("```\n# Problematic Code:\n" + issue.get("original_code") + "\n```")
            if issue.get("fixed_code"):
                md.append("```\n# Suggested Fix:\n" + issue.get("fixed_code") + "\n```")
            md.append("---\n")

    if review.get("improved_code"):
        md.append("## 💡 Complete Refactored Code")
        md.append(f"```{language.lower()}\n{review.get('improved_code')}\n```\n")
        
    if test_cases:
        md.append("## 🧪 Recommended Unit Tests")
        for tc in test_cases:
            md.append(f"### Test: `{tc.get('name', 'test_case')}`")
            md.append(f"*{tc.get('description', '')}*")
            if tc.get("code"):
                md.append(f"```{language.lower()}\n{tc.get('code')}\n```\n")

    return "\n".join(md)

def export_to_json(review: dict) -> str:
    return json.dumps(review, indent=2)

def export_to_html(review: dict) -> str:
    md_content = export_to_markdown(review)
    # Simple self-contained standalone HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Code Review Report - {review.get('title', 'Report')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #e2e8f0; background: #0f172a; padding: 40px; max-width: 900px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        pre {{ background: #1e293b; padding: 16px; border-radius: 8px; overflow-x: auto; border: 1px solid #334155; }}
        code {{ font-family: "JetBrains Mono", Consolas, monospace; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #334155; padding: 10px; text-align: left; }}
        th {{ background: #1e293b; color: #38bdf8; }}
        hr {{ border: none; border-top: 1px solid #334155; margin: 30px 0; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
    </style>
</head>
<body>
    <pre style="white-space: pre-wrap; font-family: inherit;">{md_content}</pre>
</body>
</html>"""
