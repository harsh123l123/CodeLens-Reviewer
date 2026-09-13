// Monaco Editor Management

let editorInstance = null;
let currentDecorations = [];

export function initMonaco(containerId, initialCode = "", language = "python") {
  return new Promise((resolve, reject) => {
    if (typeof window.require === "undefined") {
      reject(new Error("Monaco AMD loader not loaded"));
      return;
    }

    window.require.config({
      paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" }
    });

    window.require(["vs/editor/editor.main"], function () {
      const container = document.getElementById(containerId);
      if (!container) {
        reject(new Error(`Container #${containerId} not found`));
        return;
      }

      // Define sleek dark theme
      monaco.editor.defineTheme("cyber-dark", {
        base: "vs-dark",
        inherit: true,
        rules: [
          { token: "comment", foreground: "64748b", fontStyle: "italic" },
          { token: "keyword", foreground: "a855f7", fontStyle: "bold" },
          { token: "string", foreground: "34d399" },
          { token: "number", foreground: "f59e0b" },
          { token: "function", foreground: "38bdf8" }
        ],
        colors: {
          "editor.background": "#0d1424",
          "editor.lineHighlightBackground": "#162238",
          "editorLineNumber.foreground": "#475569",
          "editorLineNumber.activeForeground": "#818cf8",
          "editorCursor.foreground": "#6366f1",
          "editor.selectionBackground": "#312e81"
        }
      });

      editorInstance = monaco.editor.create(container, {
        value: initialCode,
        language: mapLanguageToMonaco(language),
        theme: "cyber-dark",
        automaticLayout: true,
        fontSize: 13,
        fontFamily: "'JetBrains Mono', Consolas, 'Courier New', monospace",
        minimap: { enabled: true, scale: 1 },
        scrollBeyondLastLine: false,
        renderLineHighlight: "all",
        tabSize: 4,
        cursorBlinking: "smooth",
        cursorSmoothCaretAnimation: "on"
      });

      // Update status bar on cursor movement
      editorInstance.onDidChangeCursorPosition((e) => {
        const lineEl = document.getElementById("status-line-col");
        if (lineEl) {
          lineEl.textContent = `Ln ${e.position.lineNumber}, Col ${e.position.column}`;
        }
      });

      // Update lines count on model content changes
      editorInstance.onDidChangeModelContent(() => {
        const countEl = document.getElementById("status-lines-count");
        if (countEl) {
          countEl.textContent = `${editorInstance.getModel().getLineCount()} lines`;
        }
      });

      resolve(editorInstance);
    });
  });
}

export function getEditorValue() {
  return editorInstance ? editorInstance.getValue() : "";
}

export function setEditorValue(code) {
  if (editorInstance) {
    editorInstance.setValue(code);
  }
}

export function setEditorLanguage(language) {
  if (editorInstance) {
    const model = editorInstance.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, mapLanguageToMonaco(language));
    }
  }
}

export function jumpToLine(lineNumber) {
  if (!editorInstance || !lineNumber) return;
  
  editorInstance.revealLineInCenter(lineNumber, monaco.editor.ScrollType.Smooth);
  editorInstance.setPosition({ lineNumber, column: 1 });
  editorInstance.focus();

  // Clear previous line highlights & add new one
  currentDecorations = editorInstance.deltaDecorations(currentDecorations, [
    {
      range: new monaco.Range(lineNumber, 1, lineNumber, 1),
      options: {
        isWholeLine: true,
        className: "monaco-highlight-line monaco-highlight-pulse",
        glyphMarginClassName: "monaco-glyph-error"
      }
    }
  ]);
}

export function applyFixToEditor(originalSnippet, fixedSnippet) {
  if (!editorInstance) return false;
  const model = editorInstance.getModel();
  const currentContent = model.getValue();

  if (originalSnippet && currentContent.includes(originalSnippet)) {
    const match = model.findMatches(originalSnippet, false, false, false, null, true);
    if (match.length > 0) {
      editorInstance.executeEdits("code-reviewer-fix", [
        {
          range: match[0].range,
          text: fixedSnippet,
          forceMoveMarkers: true
        }
      ]);
      editorInstance.pushUndoStop();
      return true;
    }
  }
  return false;
}

function mapLanguageToMonaco(lang) {
  const map = {
    python: "python",
    javascript: "javascript",
    typescript: "typescript",
    php: "php",
    go: "go",
    java: "java",
    cpp: "cpp",
    c: "c",
    csharp: "csharp",
    rust: "rust",
    sql: "sql",
    html: "html",
    css: "css",
    json: "json"
  };
  return map[lang.toLowerCase()] || "plaintext";
}
