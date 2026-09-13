// CodeLens AI - API Client Service

const API_BASE = ""; // Relative to server origin

export const api = {
  async reviewCode({ code, language, apiKey, model, title }) {
    const res = await fetch(`${API_BASE}/api/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        language,
        api_key: apiKey,
        model,
        title
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP error ${res.status}`);
    }
    return res.json();
  },

  async getDiff({ original, modified }) {
    const res = await fetch(`${API_BASE}/api/diff`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original, modified })
    });
    if (!res.ok) throw new Error("Failed to calculate diff");
    return res.json();
  },

  async getSamples() {
    const res = await fetch(`${API_BASE}/api/samples`);
    if (!res.ok) throw new Error("Failed to load code samples");
    return res.json();
  },

  async getHistory() {
    const res = await fetch(`${API_BASE}/api/history`);
    if (!res.ok) throw new Error("Failed to load review history");
    return res.json();
  },

  async getReviewById(id) {
    const res = await fetch(`${API_BASE}/api/history/${id}`);
    if (!res.ok) throw new Error("Review not found");
    return res.json();
  },

  async deleteReview(id) {
    const res = await fetch(`${API_BASE}/api/history/${id}`, { method: "DELETE" });
    return res.ok;
  },

  async toggleBookmark(id) {
    const res = await fetch(`${API_BASE}/api/bookmark/${id}`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to update bookmark");
    return res.json();
  },

  async exportReport(review, format = "markdown") {
    const res = await fetch(`${API_BASE}/api/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review, format })
    });
    if (!res.ok) throw new Error("Failed to generate export");
    return res.json();
  }
};
