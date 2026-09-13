import difflib

def generate_unified_diff(original: str, modified: str, fromfile: str = "original", tofile: str = "reviewed") -> str:
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(orig_lines, mod_lines, fromfile=fromfile, tofile=tofile)
    return "".join(diff)

def generate_split_diff(original: str, modified: str) -> dict:
    orig_lines = original.splitlines()
    mod_lines = modified.splitlines()
    
    matcher = difflib.SequenceMatcher(None, orig_lines, mod_lines)
    diff_rows = []
    
    added_count = 0
    deleted_count = 0
    
    orig_line_no = 1
    mod_line_no = 1
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for o_idx, m_idx in zip(range(i1, i2), range(j1, j2)):
                diff_rows.append({
                    "type": "equal",
                    "old_line_no": orig_line_no,
                    "new_line_no": mod_line_no,
                    "old_text": orig_lines[o_idx],
                    "new_text": mod_lines[m_idx]
                })
                orig_line_no += 1
                mod_line_no += 1
        elif tag == 'replace':
            # Highlight replacements
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                has_old = (i1 + k) < i2
                has_new = (j1 + k) < j2
                
                old_no = orig_line_no if has_old else None
                new_no = mod_line_no if has_new else None
                
                old_text = orig_lines[i1 + k] if has_old else ""
                new_text = mod_lines[j1 + k] if has_new else ""
                
                diff_rows.append({
                    "type": "modified",
                    "old_line_no": old_no,
                    "new_line_no": new_no,
                    "old_text": old_text,
                    "new_text": new_text
                })
                
                if has_old:
                    orig_line_no += 1
                    deleted_count += 1
                if has_new:
                    mod_line_no += 1
                    added_count += 1
        elif tag == 'delete':
            for o_idx in range(i1, i2):
                diff_rows.append({
                    "type": "delete",
                    "old_line_no": orig_line_no,
                    "new_line_no": None,
                    "old_text": orig_lines[o_idx],
                    "new_text": ""
                })
                orig_line_no += 1
                deleted_count += 1
        elif tag == 'insert':
            for m_idx in range(j1, j2):
                diff_rows.append({
                    "type": "insert",
                    "old_line_no": None,
                    "new_line_no": mod_line_no,
                    "old_text": "",
                    "new_text": mod_lines[m_idx]
                })
                mod_line_no += 1
                added_count += 1
                
    return {
        "unified": generate_unified_diff(original, modified),
        "rows": diff_rows,
        "stats": {
            "additions": added_count,
            "deletions": deleted_count,
            "total_changes": added_count + deleted_count
        }
    }
