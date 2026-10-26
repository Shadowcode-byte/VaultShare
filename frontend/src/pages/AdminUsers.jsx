import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import AdminLayout from "../components/AdminLayout";
import { Alert, Badge, Spinner } from "../components/ui";
import { formatDate } from "../lib/format";

export default function AdminUsers() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = () => {
    api.adminUsers().then(setUsers).catch(() => setUsers([]));
  };

  useEffect(load, []);

  const toggleStatus = async (u) => {
    const newStatus = u.status === "active" ? "disabled" : "active";
    const verb = newStatus === "disabled" ? "disable" : "re-enable";
    if (!window.confirm(`${verb === "disable" ? "Disable" : "Re-enable"} ${u.email}?`)) return;

    setError("");
    setBusyId(u.id);
    try {
      await api.adminUpdateUserStatus(u.id, newStatus);
      load();
    } catch (err) {
      setError(err.detail || `Could not ${verb} this account.`);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <AdminLayout title="User Management" subtitle="Disabling an account takes effect immediately, even on an already-open session.">
      <div className="mb-4"><Alert>{error}</Alert></div>

      {users === null ? (
        <Spinner />
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs text-slate-400">
                <th className="px-5 py-2.5 font-medium">Name</th>
                <th className="px-5 py-2.5 font-medium">Email</th>
                <th className="px-5 py-2.5 font-medium">Role</th>
                <th className="px-5 py-2.5 font-medium">Status</th>
                <th className="px-5 py-2.5 font-medium">Joined</th>
                <th className="px-5 py-2.5 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === currentUser.id;
                return (
                  <tr key={u.id} className="border-b border-slate-50 last:border-0">
                    <td className="px-5 py-3 font-medium text-slate-700">{u.name}</td>
                    <td className="px-5 py-3 text-slate-500">{u.email}</td>
                    <td className="px-5 py-3">
                      <Badge tone={u.role === "admin" ? "navy" : "gray"}>{u.role}</Badge>
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone={u.status === "active" ? "green" : "red"}>{u.status}</Badge>
                    </td>
                    <td className="px-5 py-3 text-slate-500">{formatDate(u.created_at)}</td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => toggleStatus(u)}
                        disabled={isSelf || busyId === u.id}
                        title={isSelf ? "You cannot change your own account status" : undefined}
                        className="text-xs font-medium text-navy hover:underline disabled:cursor-not-allowed disabled:text-slate-300 disabled:no-underline"
                      >
                        {u.status === "active" ? "Disable" : "Re-enable"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </AdminLayout>
  );
}
