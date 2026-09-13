// Diff Viewer Rendering Engine

export function renderDiffView(containerId, diffData, onAcceptAll) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!diffData || !diffData.rows || diffData.rows.length === 0) {
    container.innerHTML = `
      <div style="padding: 40px; text-align: center; color: var(--text-muted);">
        <p>No changes or diff available yet.</p>
        <p style="font-size: 12px; margin-top: 6px;">Run a review or load code with suggested fixes to see the diff comparison.</p>
      </div>
    `;
    return;
  }

  const stats = diffData.stats || { additions: 0, deletions: 0 };
  
  let html = `
    <div class="diff-header-bar">
      <div class="diff-stats-group">
        <span class="diff-stat-item diff-add">+${stats.additions} additions</span>
        <span class="diff-stat-item diff-del">-${stats.deletions} deletions</span>
      </div>
      <div>
        <button id="btn-accept-diff" class="btn btn-primary btn-sm">
          Apply All Changes to Editor
        </button>
      </div>
    </div>
    
    <div class="split-diff-wrapper">
      <!-- Original Side -->
      <div class="split-diff-pane">
        <div class="split-pane-header">Original Code</div>
        <table class="diff-table">
          <tbody>
  `;

  diffData.rows.forEach(row => {
    const typeClass = row.type === 'delete' ? 'delete' : (row.type === 'modified' ? 'modified' : 'equal');
    const lineNo = row.old_line_no !== null && row.old_line_no !== undefined ? row.old_line_no : '';
    const text = escapeHtml(row.old_text || '');
    html += `
      <tr class="diff-row ${typeClass}">
        <td class="diff-gutter">${lineNo}</td>
        <td class="diff-content">${text}</td>
      </tr>
    `;
  });

  html += `
          </tbody>
        </table>
      </div>
      
      <!-- Reviewed / Fixed Side -->
      <div class="split-diff-pane">
        <div class="split-pane-header">Refactored / Fixed Code</div>
        <table class="diff-table">
          <tbody>
  `;

  diffData.rows.forEach(row => {
    const typeClass = row.type === 'insert' ? 'insert' : (row.type === 'modified' ? 'modified' : 'equal');
    const lineNo = row.new_line_no !== null && row.new_line_no !== undefined ? row.new_line_no : '';
    const text = escapeHtml(row.new_text || '');
    html += `
      <tr class="diff-row ${typeClass}">
        <td class="diff-gutter">${lineNo}</td>
        <td class="diff-content">${text}</td>
      </tr>
    `;
  });

  html += `
          </tbody>
        </table>
      </div>
    </div>
  `;

  container.innerHTML = html;

  const acceptBtn = document.getElementById("btn-accept-diff");
  if (acceptBtn && onAcceptAll) {
    acceptBtn.addEventListener("click", onAcceptAll);
  }
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
