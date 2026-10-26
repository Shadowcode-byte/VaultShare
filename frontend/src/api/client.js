const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || "Request failed");
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Every call sets credentials: "include" — this is what makes the
 * browser send the HttpOnly session cookie set by the backend on
 * login. Without it, every request after login would look
 * unauthenticated no matter what the backend does, because a cookie
 * from a previous response is never automatically attached to
 * cross-origin fetches unless explicitly asked for.
 */
async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: options.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });

  if (res.status === 204) return null;

  let data = null;
  try {
    data = await res.json();
  } catch {
    // some responses (file downloads) aren't JSON — handled by callers directly
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    if (typeof data?.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data?.detail)) {
      // FastAPI/Pydantic validation errors (422) come back as a list of
      // {loc, msg, type} objects, not a plain string — this is a
      // different shape from our own HTTPException(detail="...") calls,
      // which are always plain strings. Both need to end up readable.
      message = data.detail.map((d) => d.msg).join("; ");
    }
    throw new ApiError(res.status, message);
  }
  return data;
}

export const api = {
  // ---- auth ----
  register: (name, email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/auth/me"),

  // ---- files ----
  uploadFile: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/files/upload", { method: "POST", body: form });
  },
  myFiles: () => request("/files/mine"),
  sharedWithMe: () => request("/files/shared-with-me"),
  fileDetails: (fileId) => request(`/files/${fileId}`),
  verifyIntegrity: (fileId) => request(`/files/${fileId}/verify-integrity`),
  listShares: (fileId) => request(`/files/${fileId}/shares`),
  shareFile: (fileId, email, permission) =>
    request(`/files/${fileId}/share`, { method: "POST", body: JSON.stringify({ email, permission }) }),
  revokeShare: (fileId, userId) =>
    request(`/files/${fileId}/share/${userId}`, { method: "DELETE" }),
  deleteFile: (fileId) => request(`/files/${fileId}`, { method: "DELETE" }),

  /** Downloads return raw bytes, not JSON — handled separately from
   * the generic request() helper above so the file's actual content
   * type and filename survive intact. */
  async downloadFile(fileId, filename) {
    const res = await fetch(`${API_BASE}/files/${fileId}/download`, { credentials: "include" });
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      throw new ApiError(res.status, data?.detail || "Download failed");
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "download";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  // ---- admin ----
  adminUsers: () => request("/admin/users"),
  adminUpdateUserStatus: (userId, status) =>
    request(`/admin/users/${userId}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  adminAuditLogs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/admin/audit-logs${qs ? `?${qs}` : ""}`);
  },
  adminStats: () => request("/admin/stats"),
};

export { ApiError };
