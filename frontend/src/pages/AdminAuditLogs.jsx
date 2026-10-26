import { useEffect, useState } from "react";
import { api } from "../api/client";
import AdminLayout from "../components/AdminLayout";
import { Badge, Button, Spinner } from "../components/ui";

const ACTIONS = [
  "USER_REGISTERED", "USER_LOGIN", "USER_LOGIN_FAILED", "USER_LOGOUT",
  "FILE_UPLOADED", "FILE_ACCESSED", "FILE_DOWNLOADED", "FILE_SHARED",
  "FILE_ACCESS_REVOKED", "FILE_DELETED", "UNAUTHORIZED_ACCESS_ATTEMPT",
  "INTEGRITY_CHECK_FAILED", "ACCOUNT_STATUS_CHANGED",
];
const RESULTS = ["success", "failure", "denied"];
const PAGE_SIZE = 25;

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState(null);
  const [action, setAction] = useState("");
  const [result, setResult] = useState("");
  const [page, setPage] = useState(0);

  const load = () => {
    setLogs(null);
    const params = { limit: PAGE_SIZE, offset: page * PAGE_SIZE };
    if (action) params.action = action;
    if (result) params.result = result;
    api.adminAuditLogs(params).then(setLogs).catch(() => setLogs([]));
  };

  useEffect(load, [action, result, page]);

  const changeFilter = (setter) => (e) => {
    setPage(0);
    setter(e.target.value);
  };

  return (
    <AdminLayout
      title="Audit Logs"
      subtitle="Every sensitive action, filterable by type and outcome."
      actions={
        <>
          <select value={action} onChange={changeFilter(setAction)} className="input w-48">
            <option value="">All actions</option>
            {ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <select value={result} onChange={changeFilter(setResult)} className="input w-36">
            <option value="">All results</option>
            {RESULTS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </>
      }
    >
      {logs === null ? (
        <Spinner />
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs text-slate-400">
                  <th className="px-5 py-2.5 font-medium">Time</th>
                  <th className="px-5 py-2.5 font-medium">User</th>
                  <th className="px-5 py-2.5 font-medium">Action</th>
                  <th className="px-5 py-2.5 font-medium">Result</th>
                  <th className="px-5 py-2.5 font-medium">File</th>
                  <th className="px-5 py-2.5 font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-400">No matching log entries.</td></tr>
                ) : (
                  logs.map((e) => (
                    <tr key={e.id} className="border-b border-slate-50 last:border-0 align-top">
                      <td className="px-5 py-2.5 whitespace-nowrap text-slate-500">{new Date(e.timestamp).toLocaleString()}</td>
                      <td className="px-5 py-2.5 text-slate-700">{e.user_email || "—"}</td>
                      <td className="px-5 py-2.5 font-mono text-xs text-slate-600">{e.action}</td>
                      <td className="px-5 py-2.5">
                        <Badge tone={e.result === "success" ? "green" : e.result === "denied" ? "gray" : "red"}>
                          {e.result}
                        </Badge>
                      </td>
                      <td className="px-5 py-2.5 font-mono text-xs text-slate-400">
                        {e.file_id ? `${e.file_id.slice(0, 8)}…` : "—"}
                      </td>
                      <td className="px-5 py-2.5 max-w-xs truncate text-xs text-slate-400">
                        {e.event_metadata ? JSON.stringify(e.event_metadata) : ""}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <p className="text-xs text-slate-400">Page {page + 1}</p>
            <div className="flex gap-2">
              <Button variant="secondary" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <Button variant="secondary" disabled={logs.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </AdminLayout>
  );
}
