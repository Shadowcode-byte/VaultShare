import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import Layout from "../components/Layout";
import { formatBytes, formatDate, fileIcon } from "../lib/format";
import { Alert, Badge, Button, Spinner } from "../components/ui";

export default function FileDetails() {
  const { fileId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [shares, setShares] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [integrityMsg, setIntegrityMsg] = useState(null);
  const [downloadError, setDownloadError] = useState("");

  const isOwner = file && user && file.owner_id === user.id;

  const loadFile = () => {
    api.fileDetails(fileId).then(setFile).catch(() => setNotFound(true));
  };

  useEffect(loadFile, [fileId]);

  useEffect(() => {
    if (isOwner) {
      api.listShares(fileId).then(setShares).catch(() => setShares([]));
    }
  }, [fileId, isOwner]);

  const handleDownload = async () => {
    setDownloadError("");
    setDownloading(true);
    try {
      await api.downloadFile(fileId, file.original_filename);
    } catch (err) {
      setDownloadError(err.detail || "Download failed.");
    } finally {
      setDownloading(false);
    }
  };

  const handleVerify = async () => {
    setIntegrityMsg(null);
    try {
      await api.verifyIntegrity(fileId);
      setIntegrityMsg({ kind: "success", text: "Integrity check passed — file matches its stored fingerprint." });
    } catch (err) {
      setIntegrityMsg({ kind: "error", text: err.detail || "Integrity check failed." });
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Permanently delete "${file.original_filename}"? This cannot be undone, and anyone it was shared with will lose access immediately.`)) {
      return;
    }
    try {
      await api.deleteFile(fileId);
      navigate("/files", { replace: true });
    } catch (err) {
      setDownloadError(err.detail || "Could not delete this file.");
    }
  };

  if (notFound) {
    return (
      <Layout title="File Not Found">
        <Alert>This file doesn't exist, or you don't have access to it.</Alert>
      </Layout>
    );
  }

  if (!file) {
    return (
      <Layout>
        <Spinner />
      </Layout>
    );
  }

  return (
    <Layout title={file.original_filename} subtitle={`${formatBytes(file.file_size)} · Uploaded ${formatDate(file.created_at)}`}>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{fileIcon(file.file_type)}</span>
              <div>
                <p className="font-medium text-slate-800">{file.original_filename}</p>
                <p className="text-xs text-slate-400 font-mono">SHA-256: {file.sha256_hash.slice(0, 24)}…</p>
              </div>
              {isOwner && <Badge tone="ice">Owner</Badge>}
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <Button onClick={handleDownload} disabled={downloading}>
                {downloading ? "Decrypting…" : "Download"}
              </Button>
              <Button variant="secondary" onClick={handleVerify}>
                Check Integrity
              </Button>
              {isOwner && (
                <Button variant="danger" onClick={handleDelete} className="ml-auto">
                  Delete File
                </Button>
              )}
            </div>

            <div className="mt-3 space-y-2">
              <Alert kind="error">{downloadError}</Alert>
              {integrityMsg && <Alert kind={integrityMsg.kind}>{integrityMsg.text}</Alert>}
            </div>
          </section>

          {isOwner && <SharingPanel fileId={fileId} shares={shares} onChange={() => api.listShares(fileId).then(setShares)} />}
        </div>

        <aside className="rounded-lg border border-slate-200 bg-white p-6 h-fit">
          <h3 className="font-serif text-base font-bold text-navy">Details</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <Row label="Type" value={file.file_type} />
            <Row label="Size" value={formatBytes(file.file_size)} />
            <Row label="Uploaded" value={formatDate(file.created_at)} />
          </dl>
        </aside>
      </div>
    </Layout>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between border-b border-slate-100 pb-2">
      <dt className="text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-700">{value}</dd>
    </div>
  );
}

function SharingPanel({ fileId, shares, onChange }) {
  const [email, setEmail] = useState("");
  const [permission, setPermission] = useState("view");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleShare = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      await api.shareFile(fileId, email, permission);
      setSuccess(`Shared with ${email}.`);
      setEmail("");
      onChange();
    } catch (err) {
      setError(err.detail || "Could not share this file.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (userId) => {
    try {
      await api.revokeShare(fileId, userId);
      onChange();
    } catch {
      // Failing silently here just means the list won't refresh; the
      // user can retry. Not worth a modal for this.
    }
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6">
      <h3 className="font-serif text-base font-bold text-navy">Sharing</h3>

      <form onSubmit={handleShare} className="mt-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[220px]">
          <label className="mb-1 block text-xs font-medium text-slate-500">Student's email</label>
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="input" placeholder="rahul@upes.ac.in"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Access</label>
          <select value={permission} onChange={(e) => setPermission(e.target.value)} className="input">
            <option value="view">View Only</option>
            <option value="download">Can Download</option>
          </select>
        </div>
        <Button type="submit" disabled={submitting}>Share</Button>
      </form>

      <div className="mt-2 space-y-2">
        <Alert kind="error">{error}</Alert>
        <Alert kind="success">{success}</Alert>
      </div>

      <div className="mt-5">
        {shares === null ? (
          <Spinner />
        ) : shares.length === 0 ? (
          <p className="text-sm text-slate-400">Not shared with anyone yet.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {shares.map((s) => (
              <li key={s.user_id} className="flex items-center justify-between py-2.5">
                <div>
                  <p className="text-sm font-medium text-slate-700">{s.name}</p>
                  <p className="text-xs text-slate-400">{s.email}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge tone={s.permission === "download" ? "navy" : "gray"}>
                    {s.permission === "download" ? "Can Download" : "View Only"}
                  </Badge>
                  <button
                    onClick={() => handleRevoke(s.user_id)}
                    className="text-xs font-medium text-red-500 hover:underline"
                  >
                    Revoke
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
