// Main Application Controller

import { api } from "./api.js";
import { initMonaco, getEditorValue, setEditorValue, setEditorLanguage, jumpToLine, applyFixToEditor } from "./editor.js";
import { renderDiffView } from "./diff_viewer.js";
import { renderScorecard, renderIssues, renderFilterPills, renderUnitTests } from "./review_ui.js";

let initialModel = localStorage.getItem("gemini_model") || "gemini-3.6-flash";
if (initialModel === "gemini-2.5-flash") {
  initialModel = "gemini-3.6-flash";
  localStorage.setItem("gemini_model", "gemini-3.6-flash");
}

// Global Application State
const state = {
  currentReview: null,
  language: "python",
  apiKey: localStorage.getItem("gemini_api_key") || "",
  model: initialModel,
  editorMode: "editor", // 'editor' | 'diff'
  activeTab: "overview",
  issuesFilter: "all",
  activeFileName: "Untitled"
};

const IGNORED_DIRS = new Set([
  ".git", ".github", "node_modules", "__pycache__", ".vscode", ".idea",
  "dist", "build", ".next", ".nuxt", "target", "vendor", ".cache", ".gemini"
]);

const EXTENSION_MAP = {
  py: "python",
  js: "javascript",
  jsx: "javascript",
  ts: "typescript",
  tsx: "typescript",
  php: "php",
  go: "go",
  java: "java",
  cpp: "cpp",
  c: "c",
  h: "c",
  hpp: "cpp",
  cs: "csharp",
  rs: "rust",
  sql: "sql",
  html: "html",
  css: "css",
  json: "json",
  md: "markdown",
  txt: "plaintext",
  sh: "shell",
  yaml: "yaml",
  yml: "yaml",
  xml: "xml"
};

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Initialize Monaco Editor with clean placeholder
  try {
    const initialCode = `# Paste your code directly here, upload a file, or open a project folder.
# Click "Review Code" to analyze security vulnerabilities, bugs, and get instant solutions.

def calculate_discount(price, discount_percent):
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid discount percentage")
    return price - (price * (discount_percent / 100))
`;
    await initMonaco("monaco-editor-wrapper", initialCode, state.language);
  } catch (err) {
    console.error("Monaco initialization error:", err);
  }

  // 2. Setup event listeners & systems
  setupEventListeners();
  setupPaneResizer();
  setupDragAndDrop();
  setupFileInput();
  setupFolderInput();
  setupSidebar();
});

function setupEventListeners() {
  // Run Review Code Button
  const btnRunReview = document.getElementById("btn-run-review");
  if (btnRunReview) {
    btnRunReview.addEventListener("click", handleRunReview);
  }

  // Language Select
  const selectLang = document.getElementById("select-language");
  if (selectLang) {
    selectLang.addEventListener("change", (e) => {
      state.language = e.target.value;
      setEditorLanguage(state.language);
      showToast(`Language set to ${state.language}`);
    });
  }

  // Clear Code Button
  const btnClear = document.getElementById("btn-clear-code");
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      setEditorValue("");
      updateActiveFilename("Untitled");
      showToast("Editor cleared - ready for paste or upload");
    });
  }

  // Segmented Mode Switcher (Editor vs Diff)
  document.querySelectorAll(".segmented-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-mode");
      setEditorMode(mode);
    });
  });

  // Review Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      switchTab(tab);
    });
  });

  // Settings Modal
  const btnSettings = document.getElementById("btn-settings");
  const modalSettings = document.getElementById("modal-settings");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const btnCloseSettings = document.getElementById("btn-close-settings");
  const inputApiKey = document.getElementById("input-api-key");
  const selectModel = document.getElementById("select-model");

  if (btnSettings && modalSettings) {
    btnSettings.addEventListener("click", () => {
      if (inputApiKey) inputApiKey.value = state.apiKey;
      if (selectModel) selectModel.value = state.model;
      modalSettings.classList.add("open");
    });
  }
  if (btnCloseSettings && modalSettings) {
    btnCloseSettings.addEventListener("click", () => modalSettings.classList.remove("open"));
  }
  if (btnSaveSettings && modalSettings) {
    btnSaveSettings.addEventListener("click", () => {
      state.apiKey = (inputApiKey ? inputApiKey.value.trim() : "");
      state.model = (selectModel ? selectModel.value : "gemini-3.6-flash");
      localStorage.setItem("gemini_api_key", state.apiKey);
      localStorage.setItem("gemini_model", state.model);
      modalSettings.classList.remove("open");
      showToast(state.apiKey ? "Gemini API key configured" : "Using local static & security analysis engine");
    });
  }

  // Export Modal
  const btnExport = document.getElementById("btn-export");
  const modalExport = document.getElementById("modal-export");
  const btnCloseExport = document.getElementById("btn-close-export");
  const btnDownloadExport = document.getElementById("btn-download-export");
  const selectExportFormat = document.getElementById("select-export-format");

  if (btnExport && modalExport) {
    btnExport.addEventListener("click", () => {
      if (!state.currentReview) {
        showToast("Please review code first before exporting.", "error");
        return;
      }
      modalExport.classList.add("open");
    });
  }
  if (btnCloseExport && modalExport) {
    btnCloseExport.addEventListener("click", () => modalExport.classList.remove("open"));
  }
  if (btnDownloadExport && modalExport) {
    btnDownloadExport.addEventListener("click", async () => {
      const format = selectExportFormat ? selectExportFormat.value : "markdown";
      try {
        const res = await api.exportReport(state.currentReview, format);
        downloadFile(res.content, `codelens-review-${Date.now()}.${format === 'markdown' ? 'md' : format}`, res.mime);
        modalExport.classList.remove("open");
        showToast(`Exported report as ${format.toUpperCase()}`);
      } catch (err) {
        showToast("Export failed: " + err.message, "error");
      }
    });
  }
}

// Single File Upload Setup
function setupFileInput() {
  const btnUpload = document.getElementById("btn-upload-file");
  const fileInput = document.getElementById("file-input");

  if (btnUpload && fileInput) {
    btnUpload.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        loadFileIntoEditor(files[0]);
        fileInput.value = "";
      }
    });
  }
}

// Folder Selection & Project Tree Setup
function setupFolderInput() {
  const btnOpenFolder = document.getElementById("btn-open-folder");
  const btnOpenFolderCta = document.getElementById("btn-open-folder-cta");
  const folderInput = document.getElementById("folder-input");

  const triggerFolder = () => {
    if (folderInput) folderInput.click();
  };

  if (btnOpenFolder) btnOpenFolder.addEventListener("click", triggerFolder);
  if (btnOpenFolderCta) btnOpenFolderCta.addEventListener("click", triggerFolder);

  if (folderInput) {
    folderInput.addEventListener("change", (e) => {
      const files = Array.from(e.target.files || []);
      if (files.length === 0) return;
      handleFolderFiles(files);
      folderInput.value = "";
    });
  }
}

// Sidebar Expand / Collapse Toggle
function setupSidebar() {
  const sidebar = document.getElementById("sidebar-pane");
  const btnToggle = document.getElementById("btn-toggle-sidebar");
  const btnExpand = document.getElementById("btn-expand-sidebar");

  if (btnToggle && sidebar) {
    btnToggle.addEventListener("click", () => {
      sidebar.classList.add("collapsed");
      if (btnExpand) btnExpand.style.display = "inline-flex";
    });
  }

  if (btnExpand && sidebar) {
    btnExpand.addEventListener("click", () => {
      sidebar.classList.remove("collapsed");
      btnExpand.style.display = "none";
    });
  }
}

function handleFolderFiles(files) {
  // Filter readable code files & exclude junk
  const validFiles = files.filter(f => {
    const relPath = f.webkitRelativePath || f.name;
    const parts = relPath.split('/');
    for (const p of parts) {
      if (IGNORED_DIRS.has(p) || (p.startsWith('.') && p !== '.env')) {
        return false;
      }
    }
    const ext = f.name.split('.').pop().toLowerCase();
    return Boolean(EXTENSION_MAP[ext]);
  });

  if (validFiles.length === 0) {
    showToast("No supported code files found in selected folder.", "error");
    return;
  }

  // Build tree structure
  const rootTree = { name: "root", isFolder: true, children: {} };

  validFiles.forEach(file => {
    const parts = (file.webkitRelativePath || file.name).split('/');
    let current = rootTree;
    for (let i = 0; i < parts.length - 1; i++) {
      const folderName = parts[i];
      if (!current.children[folderName]) {
        current.children[folderName] = { name: folderName, isFolder: true, children: {} };
      }
      current = current.children[folderName];
    }
    const fileName = parts[parts.length - 1];
    current.children[fileName] = { name: fileName, isFolder: false, file, path: file.webkitRelativePath };
  });

  // Ensure sidebar is open
  const sidebar = document.getElementById("sidebar-pane");
  const btnExpand = document.getElementById("btn-expand-sidebar");
  if (sidebar) sidebar.classList.remove("collapsed");
  if (btnExpand) btnExpand.style.display = "none";

  // Render tree
  const treeContainer = document.getElementById("file-tree-container");
  renderFileTree(rootTree, treeContainer);

  // Auto-open first file into editor
  const firstFile = findFirstCodeFile(rootTree);
  if (firstFile) {
    loadFileIntoEditor(firstFile);
  }

  showToast(`Opened folder: ${validFiles.length} code files loaded`);
}

function findFirstCodeFile(node) {
  if (!node.isFolder) return node.file;
  const children = Object.values(node.children);
  for (const child of children) {
    if (!child.isFolder) return child.file;
  }
  for (const child of children) {
    if (child.isFolder) {
      const found = findFirstCodeFile(child);
      if (found) return found;
    }
  }
  return null;
}

function renderFileTree(tree, container) {
  if (!container) return;
  container.innerHTML = "";

  const rootGroup = document.createElement("div");
  rootGroup.className = "tree-folder-group";

  function buildDom(node, parentEl) {
    if (node.isFolder) {
      const folderHeader = document.createElement("div");
      folderHeader.className = "tree-node tree-folder";
      folderHeader.innerHTML = `
        <span class="tree-icon" style="background: rgba(255, 255, 255, 0.08); color: #94a3b8;">DIR</span>
        <span style="font-weight: 600; font-size: 12px; color: var(--text-primary);">${escapeHtml(node.name)}</span>
      `;

      const childrenWrapper = document.createElement("div");
      childrenWrapper.className = "tree-folder-children";

      folderHeader.addEventListener("click", () => {
        const isHidden = childrenWrapper.style.display === "none";
        childrenWrapper.style.display = isHidden ? "flex" : "none";
      });

      parentEl.appendChild(folderHeader);
      parentEl.appendChild(childrenWrapper);

      const children = Object.values(node.children).sort((a, b) => {
        if (a.isFolder === b.isFolder) return a.name.localeCompare(b.name);
        return a.isFolder ? -1 : 1;
      });

      children.forEach(child => buildDom(child, childrenWrapper));
    } else {
      const fileItem = document.createElement("div");
      fileItem.className = "tree-node tree-file";
      const ext = node.name.split('.').pop().toLowerCase();
      const extLabel = ext.toUpperCase().slice(0, 3);
      fileItem.innerHTML = `
        <span class="tree-icon" style="background: rgba(99, 102, 241, 0.18); color: #a5b4fc;">${extLabel}</span>
        <span style="overflow: hidden; text-overflow: ellipsis;">${escapeHtml(node.name)}</span>
      `;

      fileItem.addEventListener("click", () => {
        document.querySelectorAll(".tree-node.active").forEach(el => el.classList.remove("active"));
        fileItem.classList.add("active");
        loadFileIntoEditor(node.file);
      });

      parentEl.appendChild(fileItem);
    }
  }

  // Handle single top folder
  const topKeys = Object.keys(tree.children);
  if (topKeys.length === 1 && tree.children[topKeys[0]].isFolder) {
    const rootFolder = tree.children[topKeys[0]];
    const children = Object.values(rootFolder.children).sort((a, b) => {
      if (a.isFolder === b.isFolder) return a.name.localeCompare(b.name);
      return a.isFolder ? -1 : 1;
    });
    children.forEach(child => buildDom(child, rootGroup));
  } else {
    const children = Object.values(tree.children).sort((a, b) => {
      if (a.isFolder === b.isFolder) return a.name.localeCompare(b.name);
      return a.isFolder ? -1 : 1;
    });
    children.forEach(child => buildDom(child, rootGroup));
  }

  container.appendChild(rootGroup);
}

function updateActiveFilename(name) {
  state.activeFileName = name;
  const el = document.getElementById("active-filename");
  if (el) el.textContent = name;
}

function loadFileIntoEditor(file) {
  const reader = new FileReader();
  reader.onload = (event) => {
    setEditorValue(event.target.result);
    const ext = file.name.split('.').pop().toLowerCase();
    if (EXTENSION_MAP[ext]) {
      state.language = EXTENSION_MAP[ext];
      setEditorLanguage(state.language);
      const sel = document.getElementById("select-language");
      if (sel) sel.value = state.language;
    }
    updateActiveFilename(file.name);
    setEditorMode("editor");
    showToast(`Loaded: ${file.name}`);
  };
  reader.readAsText(file);
}

// Review Code Handler: Sends code to review engine & displays problems and solutions
async function handleRunReview() {
  const code = getEditorValue();
  if (!code.trim()) {
    showToast("Editor is empty. Paste code, upload a file, or open a folder.", "error");
    return;
  }

  const btn = document.getElementById("btn-run-review");
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span class="loading-pulse">Analyzing...</span>`;
  btn.disabled = true;

  try {
    const result = await api.reviewCode({
      code,
      language: state.language,
      apiKey: state.apiKey,
      model: state.model,
      title: `${state.activeFileName || state.language.toUpperCase()} Analysis`
    });

    state.currentReview = result;
    renderReviewDashboard(result);

    const issueCount = (result.issues || []).length;
    if (issueCount > 0) {
      showToast(`Review complete: Found ${issueCount} problem${issueCount > 1 ? 's' : ''}. Solutions ready!`);
      // Automatically navigate to Problems & Solutions tab so user immediately sees what problems the code has and solutions
      switchTab("issues");
    } else {
      showToast(`Review complete. Code passed with Grade ${result.grade || 'A'}!`);
      switchTab("overview");
    }
  } catch (err) {
    showToast("Review failed: " + err.message, "error");
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
}

function renderReviewDashboard(review) {
  // 1. Render Scorecard & Metrics with navigation hook to Problems tab
  renderScorecard("tab-overview-content", review, () => switchTab("issues"));

  // 2. Render Issues (Problems & Solutions)
  const issues = review.issues || [];
  const badgeEl = document.getElementById("issues-badge-count");
  if (badgeEl) badgeEl.textContent = issues.length;

  renderFilterPills("issues-filter-bar", issues, (filter) => {
    state.issuesFilter = filter;
    const filtered = filter === "all" ? issues : issues.filter(i => (i.severity || "").toLowerCase() === filter);
    renderIssues("issues-list-container", filtered, handleJumpToLine, handleApplyFix);
  });

  renderIssues("issues-list-container", issues, handleJumpToLine, handleApplyFix);

  // 3. Render Diff View
  if (review.diff) {
    renderDiffView("diff-view-wrapper", review.diff, () => {
      if (review.improved_code) {
        setEditorValue(review.improved_code);
        setEditorMode("editor");
        showToast("Applied all proposed fixes to editor");
      }
    });
  }

  // 4. Render Unit Tests
  renderUnitTests("tab-tests-content", review.test_cases || []);
}

function handleJumpToLine(lineNumber) {
  setEditorMode("editor");
  jumpToLine(lineNumber);
  showToast(`Jumped to line ${lineNumber}`);
}

function handleApplyFix(orig, fix) {
  const success = applyFixToEditor(orig, fix);
  if (success) {
    showToast("Solution applied directly to code in editor");
  } else {
    showToast("Could not auto-locate snippet. Check Diff Comparison tab.", "error");
  }
}

function setEditorMode(mode) {
  state.editorMode = mode;
  document.querySelectorAll(".segmented-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-mode") === mode);
  });

  const editorWrapper = document.getElementById("monaco-editor-wrapper");
  const diffWrapper = document.getElementById("diff-view-wrapper");

  if (mode === "diff") {
    if (editorWrapper) editorWrapper.style.display = "none";
    if (diffWrapper) diffWrapper.classList.add("active");
  } else {
    if (editorWrapper) editorWrapper.style.display = "block";
    if (diffWrapper) diffWrapper.classList.remove("active");
  }
}

function switchTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabName);
  });

  document.querySelectorAll(".tab-content").forEach(panel => {
    panel.classList.toggle("active", panel.getAttribute("id") === `tab-${tabName}`);
  });
}


function setupPaneResizer() {
  const resizer = document.getElementById("pane-resizer");
  const leftPane = document.getElementById("editor-pane");
  const container = document.getElementById("workspace-container");

  if (!resizer || !leftPane || !container) return;

  let isDragging = false;

  resizer.addEventListener("mousedown", () => {
    isDragging = true;
    resizer.classList.add("dragging");
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const containerRect = container.getBoundingClientRect();
    const newLeftWidth = e.clientX - containerRect.left;
    if (newLeftWidth > 260 && newLeftWidth < (containerRect.width - 320)) {
      leftPane.style.flex = "none";
      leftPane.style.width = `${newLeftWidth}px`;
    }
  });

  window.addEventListener("mouseup", () => {
    if (isDragging) {
      isDragging = false;
      resizer.classList.remove("dragging");
      document.body.style.cursor = "default";
      document.body.style.userSelect = "auto";
    }
  });
}

function setupDragAndDrop() {
  const dropOverlay = document.getElementById("drop-overlay");
  const editorContainer = document.getElementById("editor-body-container");
  if (!dropOverlay || !editorContainer) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    editorContainer.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropOverlay.classList.add("dragover");
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropOverlay.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropOverlay.classList.remove("dragover");
    }, false);
  });

  dropOverlay.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      loadFileIntoEditor(files[0]);
    }
  });
}

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.style.borderColor = type === 'error' ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-glass)';
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function downloadFile(content, fileName, contentType) {
  const a = document.createElement("a");
  const file = new Blob([content], { type: contentType });
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(a.href);
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
