// UI Component Renderers for Review Dashboard

export function renderScorecard(containerId, reviewData, onNavigateToIssues) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const score = reviewData.score || 0;
  const grade = (reviewData.grade || "C").toLowerCase();
  const summary = reviewData.summary || "Review completed.";
  const metrics = reviewData.metrics || {};
  const issues = reviewData.issues || [];

  const secScore = metrics.security_score ?? 80;
  const perfScore = metrics.performance_score ?? 80;
  const maintScore = metrics.maintainability_score ?? 75;
  const complexity = metrics.cyclomatic_complexity ?? 1;
  const complexityRating = metrics.complexity_rating || "Low";

  container.innerHTML = `
    <div class="scorecard-hero">
      <div class="score-main-block">
        <div class="score-circle grade-${grade}">
          <span class="score-number">${score}</span>
          <span class="score-label">Grade ${grade.toUpperCase()}</span>
        </div>
        <div class="score-details">
          <h3>Code Health Score</h3>
          <p>${summary}</p>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">
            Engine: <strong style="color: #38bdf8;">${reviewData.source === 'gemini_ai' ? 'Google Gemini AI (' + (reviewData.model_used || 'LLM') + ')' : 'Built-in Security & Static Engine'}</strong>
            ${reviewData.warning ? `<div style="color: #f87171; font-size: 11px; margin-top: 5px; padding: 4px 8px; background: rgba(239, 68, 68, 0.12); border-radius: 4px; border: 1px solid rgba(239, 68, 68, 0.25);">AI Fallback Notice: ${escapeHtml(reviewData.warning)}</div>` : (reviewData.source !== 'gemini_ai' ? '<span style="color: var(--text-secondary); margin-left: 6px;">(Add Gemini key in .env or Settings for deep LLM reasoning)</span>' : '')}
          </div>
        </div>
      </div>
    </div>

    ${issues.length > 0 ? `
      <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: var(--radius-sm); padding: 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px;">
        <div>
          <div style="font-size: 13px; font-weight: 700; color: #f87171;">Detected ${issues.length} Problem${issues.length > 1 ? 's' : ''} with Solutions</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">Detailed issues, root cause impacts, and one-click code solutions ready.</div>
        </div>
        <button id="btn-view-problems" class="btn btn-primary btn-sm" style="flex-shrink: 0;">
          View Problems &amp; Solutions &raquo;
        </button>
      </div>
    ` : `
      <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-sm); padding: 14px; display: flex; align-items: center; justify-content: space-between;">
        <div>
          <div style="font-size: 13px; font-weight: 700; color: #34d399;">Clean Code - 0 Problems Detected</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">No security vulnerabilities or code smells found.</div>
        </div>
      </div>
    `}

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-card-header">
          <span>Security Score</span>
          <span class="metric-value" style="color: ${secScore >= 80 ? '#34d399' : (secScore >= 60 ? '#facc15' : '#f87171')}">${secScore}%</span>
        </div>
        <div class="metric-progress-bar">
          <div class="metric-progress-fill" style="width: ${secScore}%; background: ${secScore >= 80 ? '#10b981' : (secScore >= 60 ? '#eab308' : '#ef4444')};"></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-card-header">
          <span>Performance Score</span>
          <span class="metric-value" style="color: ${perfScore >= 80 ? '#34d399' : (perfScore >= 60 ? '#facc15' : '#f87171')}">${perfScore}%</span>
        </div>
        <div class="metric-progress-bar">
          <div class="metric-progress-fill" style="width: ${perfScore}%; background: ${perfScore >= 80 ? '#10b981' : (perfScore >= 60 ? '#eab308' : '#ef4444')};"></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-card-header">
          <span>Maintainability Index</span>
          <span class="metric-value" style="color: ${maintScore >= 75 ? '#34d399' : (maintScore >= 50 ? '#facc15' : '#f87171')}">${maintScore}/100</span>
        </div>
        <div class="metric-progress-bar">
          <div class="metric-progress-fill" style="width: ${maintScore}%; background: #6366f1;"></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-card-header">
          <span>Cyclomatic Complexity</span>
          <span class="metric-value" style="color: #38bdf8">${complexity} <span style="font-size: 11px; color: var(--text-muted);">(${complexityRating})</span></span>
        </div>
        <div class="metric-progress-bar">
          <div class="metric-progress-fill" style="width: ${Math.min(100, complexity * 8)}%; background: #06b6d4;"></div>
        </div>
      </div>
    </div>
  `;

  const btnViewProblems = container.querySelector("#btn-view-problems");
  if (btnViewProblems && onNavigateToIssues) {
    btnViewProblems.addEventListener("click", onNavigateToIssues);
  }
}

export function renderIssues(containerId, issues, onJumpToLine, onApplyFix) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!issues || issues.length === 0) {
    container.innerHTML = `
      <div style="padding: 30px; text-align: center; color: var(--text-muted);">
        <p style="font-weight: 600; color: #34d399; font-size: 15px;">No issues found</p>
        <p style="font-size: 12px; margin-top: 4px;">Code passed all security, quality, and performance checks.</p>
      </div>
    `;
    return;
  }

  let html = `<div class="issues-list">`;

  issues.forEach(issue => {
    const sev = (issue.severity || "info").toLowerCase();
    const cat = (issue.category || "general").toLowerCase();
    const lineStart = issue.line_start || 1;
    const lineEnd = issue.line_end || lineStart;
    const lineText = lineStart === lineEnd ? `Line ${lineStart}` : `Lines ${lineStart}-${lineEnd}`;
    
    html += `
      <div class="issue-card ${sev}" data-severity="${sev}">
        <div class="issue-card-header">
          <div class="issue-badges">
            <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
            <span class="badge badge-category">${cat.toUpperCase()}</span>
          </div>
          <span class="line-tag" data-line="${lineStart}" title="Click to jump to line in editor">
            ${lineText}
          </span>
        </div>

        <h4 class="issue-title">${escapeHtml(issue.title || 'Issue')}</h4>

        <!-- Explicit Problem Section -->
        <div class="issue-problem-box">
          <div class="box-title-problem">Problem Details (${lineText})</div>
          <p style="margin: 0; font-size: 13px; line-height: 1.5; color: var(--text-primary);">${escapeHtml(issue.description || issue.title || '')}</p>
          ${issue.impact ? `<div class="issue-impact"><strong>Impact:</strong> ${escapeHtml(issue.impact)}</div>` : ''}
          ${issue.original_code ? `
            <div style="margin-top: 8px;">
              <div style="font-size: 10px; font-weight: 700; color: #f87171; text-transform: uppercase; margin-bottom: 3px;">Problematic Code:</div>
              <pre style="margin: 0; padding: 6px 8px; background: rgba(0,0,0,0.45); border-radius: 4px; font-family: var(--font-mono); font-size: 11px; color: #fca5a5; overflow-x: auto; white-space: pre-wrap;">${formatCodeSnippet(issue.original_code)}</pre>
            </div>
          ` : ''}
        </div>

        <!-- Explicit Solution Section -->
        <div class="issue-solution-box">
          <div class="box-title-solution">Recommended Solution</div>
          <p style="margin: 0; font-size: 13px; line-height: 1.5; color: var(--text-primary);">${escapeHtml(issue.suggestion || 'Apply the recommended code fix below to resolve this problem.')}</p>
          ${issue.fixed_code && !issue.fixed_code.startsWith("#") ? `
            <div class="code-fix-block" style="margin-top: 8px;">
              <div style="font-size: 10px; font-weight: 700; color: #34d399; text-transform: uppercase; margin-bottom: 4px;">Corrected Code Replacement:</div>
              <pre style="margin: 0; color: #86efac; font-family: var(--font-mono); font-size: 11px; line-height: 1.4; white-space: pre-wrap;">${formatCodeSnippet(issue.fixed_code)}</pre>
            </div>
          ` : ''}
        </div>

        <div class="issue-actions">
          <button class="btn btn-secondary btn-sm btn-jump-line" data-line="${lineStart}">
            Jump to Line
          </button>
          ${issue.original_code && issue.fixed_code && !issue.fixed_code.startsWith("#") ? `
            <button class="btn btn-primary btn-sm btn-apply-fix" data-orig="${encodeURIComponent(issue.original_code)}" data-fix="${encodeURIComponent(issue.fixed_code)}" title="Directly replace vulnerable code in the editor">
              Apply Solution
            </button>
          ` : ''}
        </div>
      </div>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;

  // Bind Jump to Line buttons
  container.querySelectorAll(".btn-jump-line, .line-tag").forEach(el => {
    el.addEventListener("click", () => {
      const line = parseInt(el.getAttribute("data-line"), 10);
      if (line && onJumpToLine) {
        onJumpToLine(line);
      }
    });
  });

  // Bind Apply Fix buttons
  container.querySelectorAll(".btn-apply-fix").forEach(btn => {
    btn.addEventListener("click", () => {
      const orig = decodeURIComponent(btn.getAttribute("data-orig"));
      const fix = decodeURIComponent(btn.getAttribute("data-fix"));
      if (onApplyFix) {
        onApplyFix(orig, fix);
      }
    });
  });
}

export function renderFilterPills(containerId, issues, onFilterChange) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const counts = {
    all: issues.length,
    critical: issues.filter(i => (i.severity || "").toLowerCase() === "critical").length,
    high: issues.filter(i => (i.severity || "").toLowerCase() === "high").length,
    medium: issues.filter(i => (i.severity || "").toLowerCase() === "medium").length,
    low: issues.filter(i => (i.severity || "").toLowerCase() === "low").length
  };

  container.innerHTML = `
    <button class="filter-pill active" data-filter="all">All (${counts.all})</button>
    ${counts.critical ? `<button class="filter-pill" data-filter="critical" style="color: #f87171;">Critical (${counts.critical})</button>` : ''}
    ${counts.high ? `<button class="filter-pill" data-filter="high" style="color: #fb923c;">High (${counts.high})</button>` : ''}
    ${counts.medium ? `<button class="filter-pill" data-filter="medium" style="color: #facc15;">Medium (${counts.medium})</button>` : ''}
    ${counts.low ? `<button class="filter-pill" data-filter="low" style="color: #60a5fa;">Low (${counts.low})</button>` : ''}
  `;

  container.querySelectorAll(".filter-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      container.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const filter = pill.getAttribute("data-filter");
      if (onFilterChange) onFilterChange(filter);
    });
  });
}

export function renderUnitTests(containerId, testCases) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!testCases || testCases.length === 0) {
    container.innerHTML = `
      <div style="padding: 30px; text-align: center; color: var(--text-muted);">
        <p>No unit tests generated yet.</p>
        <p style="font-size: 12px; margin-top: 4px;">Run a code review to automatically generate regression & boundary tests.</p>
      </div>
    `;
    return;
  }

  let html = `<div style="display: flex; flex-direction: column; gap: 14px;">`;
  testCases.forEach((tc, idx) => {
    html += `
      <div class="issue-card" style="border-left: 3px solid var(--accent-cyan);">
        <div class="issue-card-header">
          <span class="badge" style="background: rgba(6, 182, 212, 0.15); color: #67e8f9;">TEST CASE ${idx + 1}</span>
          <button class="btn btn-secondary btn-sm btn-copy-test" data-code="${encodeURIComponent(tc.code || '')}">
            Copy Code
          </button>
        </div>
        <h4 class="issue-title" style="font-family: var(--font-mono); font-size: 13px;">${escapeHtml(tc.name || 'test_case')}</h4>
        <p class="issue-desc">${escapeHtml(tc.description || '')}</p>
        <div class="code-fix-block">
          <pre style="margin: 0; color: #cbd5e1;">${escapeHtml(tc.code || '')}</pre>
        </div>
      </div>
    `;
  });
  html += `</div>`;
  container.innerHTML = html;

  container.querySelectorAll(".btn-copy-test").forEach(btn => {
    btn.addEventListener("click", () => {
      const code = decodeURIComponent(btn.getAttribute("data-code"));
      navigator.clipboard.writeText(code).then(() => {
        btn.textContent = "Copied!";
        setTimeout(() => { btn.textContent = "Copy Code"; }, 1500);
      });
    });
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatCodeSnippet(code) {
  if (!code) return '';
  return escapeHtml(code).replace(/\\n/g, '\n');
}
