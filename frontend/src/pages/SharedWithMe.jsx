import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Layout from "../components/Layout";
import { formatBytes, formatDate, fileIcon } from "../lib/format";
import { Badge, EmptyState, Spinner } from "../components/ui";

export default function SharedWithMe() {
  const [files, setFiles] = useState(null);

  useEffect(() => {
    api.sharedWithMe().then(setFiles).catch(() => setFiles([]));
  }, []);

  return (
    <Layout title="Shared With Me" subtitle="Files other students have shared with you.">
      {files === null ? (
        <Spinner />
      ) : files.length === 0 ? (
        <EmptyState
          title="Nothing shared with you yet"
          description="When another student shares a file with your account, it will show up here."
        />
      ) : (
        <div className="space-y-3">
          {files.map((f) => (
            <Link
              key={f.id}
              to={`/files/${f.id}`}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-5 py-4 transition hover:border-navy/30 hover:shadow-sm"
            >
              <div className="flex items-center gap-4">
                <span className="text-2xl">{fileIcon(f.file_type)}</span>
                <div>
                  <p className="font-medium text-slate-800">{f.original_filename}</p>
                  <p className="text-xs text-slate-400">
                    {formatBytes(f.file_size)} · Shared by {f.owner_name} · {formatDate(f.created_at)}
                  </p>
                </div>
              </div>
              <Badge tone={f.permission === "download" ? "navy" : "gray"}>
                {f.permission === "download" ? "Can Download" : "View Only"}
              </Badge>
            </Link>
          ))}
        </div>
      )}
    </Layout>
  );
}
