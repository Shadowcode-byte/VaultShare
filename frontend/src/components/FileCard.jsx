import { Link } from "react-router-dom";
import { formatBytes, formatDate, fileIcon } from "../lib/format";
import { Badge } from "./ui";

export default function FileCard({ file, badge }) {
  return (
    <Link
      to={`/files/${file.id}`}
      className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-5 py-4 transition hover:border-navy/30 hover:shadow-sm"
    >
      <div className="flex items-center gap-4">
        <span className="text-2xl">{fileIcon(file.file_type)}</span>
        <div>
          <p className="font-medium text-slate-800">{file.original_filename}</p>
          <p className="text-xs text-slate-400">
            {formatBytes(file.file_size)} · Uploaded {formatDate(file.created_at)}
          </p>
        </div>
      </div>
      {badge && <Badge tone="ice">{badge}</Badge>}
    </Link>
  );
}
