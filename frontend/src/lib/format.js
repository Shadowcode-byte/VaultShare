export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    year: "numeric", month: "short", day: "numeric",
  });
}

export function fileIcon(extension) {
  const map = {
    ".pdf": "📄", ".docx": "📝", ".pptx": "📊", ".xlsx": "📈",
    ".txt": "📃", ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
  };
  return map[extension] || "📁";
}
