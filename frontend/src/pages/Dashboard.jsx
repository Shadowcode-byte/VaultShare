import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import Layout from "../components/Layout";
import { Button, Spinner } from "../components/ui";

export default function Dashboard() {
  const { user } = useAuth();
  const [myFiles, setMyFiles] = useState(null);
  const [shared, setShared] = useState(null);

  useEffect(() => {
    api.myFiles().then(setMyFiles).catch(() => setMyFiles([]));
    api.sharedWithMe().then(setShared).catch(() => setShared([]));
  }, []);

  const loading = myFiles === null || shared === null;

  return (
    <Layout title={`Welcome, ${user?.name}`} subtitle="Here's what's happening with your files.">
      {loading ? (
        <Spinner />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <StatCard label="Files You Own" value={myFiles.length} to="/files" />
            <StatCard label="Shared With You" value={shared.length} to="/shared-with-me" />
          </div>

          <div className="mt-8 rounded-lg border border-slate-200 bg-white p-6">
            <h2 className="font-serif text-lg font-bold text-navy">Quick Actions</h2>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link to="/files"><Button>Upload a File</Button></Link>
              <Link to="/files"><Button variant="secondary">View My Files</Button></Link>
              <Link to="/shared-with-me"><Button variant="secondary">View Shared With Me</Button></Link>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}

function StatCard({ label, value, to }) {
  return (
    <Link
      to={to}
      className="block rounded-lg border border-slate-200 bg-white p-6 transition hover:border-navy/30 hover:shadow-sm"
    >
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 font-serif text-4xl font-bold text-navy">{value}</p>
    </Link>
  );
}
