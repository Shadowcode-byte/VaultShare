import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import Layout from "../components/Layout";
import FileCard from "../components/FileCard";
import { Alert, Button, EmptyState, Spinner } from "../components/ui";

export default function MyFiles() {
  const [files, setFiles] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const loadFiles = () => {
    api.myFiles().then(setFiles).catch(() => setFiles([]));
  };

  useEffect(loadFiles, []);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      await api.uploadFile(file);
      loadFiles();
    } catch (err) {
      setError(err.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <Layout
      title="My Files"
      subtitle="Documents you've uploaded and own."
      actions={
        <>
          <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelect} />
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? "Uploading & encrypting…" : "Upload File"}
          </Button>
        </>
      }
    >
      <div className="mb-4"><Alert>{error}</Alert></div>

      {files === null ? (
        <Spinner />
      ) : files.length === 0 ? (
        <EmptyState
          title="No files yet"
          description="Upload your first document — it will be validated, encrypted, and hashed automatically."
          action={<Button onClick={() => fileInputRef.current?.click()}>Upload File</Button>}
        />
      ) : (
        <div className="space-y-3">
          {files.map((f) => (
            <FileCard key={f.id} file={f} />
          ))}
        </div>
      )}
    </Layout>
  );
}
