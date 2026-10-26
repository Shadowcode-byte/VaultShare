import { useEffect, useState } from "react";
import { api } from "../api/client";
import AdminLayout from "../components/AdminLayout";
import { Badge, Spinner } from "../components/ui";

const STAT_LABELS = [
  ["total_users", "Total Users"],
  ["total_files", "Total Files"],
  ["total_active_shares", "Active Shares"],
  ["successful_logins", "Successful Logins"],
  ["failed_login_attempts", "Failed Logins"],
  ["unauthorized_access_attempts", "Unauthorized Attempts"],
  ["integrity_check_failures", "Integrity Failures"],
];

export default function AdminOverview() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.adminStats().then(setStats).catch(() => setStats(false));
  }, []);

  return (
    <AdminLayout title="Admin Overview" subtitle="Every number below is a live COUNT(*) against the database — nothing here is estimated.">
      {stats === null ? (
        <Spinner />
      ) : stats === false ? (
        <p className="text-sm text-red-500">Could not load stats.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {STAT_LABELS.map(([key, label]) => (
              <div key={key} className="rounded-lg border border-slate-200 bg-white p-5">
                <p className="text-xs font-medium text-slate-500">{label}</p>
                <p className="mt-2 font-serif text-3xl font-bold text-navy">{stats[key]}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-3">
              <h2 className="font-serif text-base font-bold text-navy">Recent Activity</h2>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs text-slate-400">
                  <th className="px-5 py-2 font-medium">Time</th>
                  <th className="px-5 py-2 font-medium">User</th>
                  <th className="px-5 py-2 font-medium">Action</th>
                  <th className="px-5 py-2 font-medium">Result</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_events.map((e) => (
                  <tr key={e.id} className="border-b border-slate-50 last:border-0">
                    <td className="px-5 py-2.5 text-slate-500">{new Date(e.timestamp).toLocaleString()}</td>
                    <td className="px-5 py-2.5 text-slate-700">{e.user_email || "—"}</td>
                    <td className="px-5 py-2.5 font-mono text-xs text-slate-600">{e.action}</td>
                    <td className="px-5 py-2.5">
                      <Badge tone={e.result === "success" ? "green" : e.result === "denied" ? "gray" : "red"}>
                        {e.result}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </AdminLayout>
  );
}
