import { Link, useLocation } from "react-router-dom";
import Layout from "./Layout";

const tabs = [
  { to: "/admin", label: "Overview" },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/audit-logs", label: "Audit Logs" },
];

export default function AdminLayout({ title, subtitle, actions, children }) {
  const location = useLocation();

  return (
    <Layout title={title} subtitle={subtitle} actions={actions}>
      <div className="mb-6 flex gap-1 border-b border-slate-200">
        {tabs.map((t) => {
          const active = location.pathname === t.to;
          return (
            <Link
              key={t.to}
              to={t.to}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
                active
                  ? "border-navy text-navy"
                  : "border-transparent text-slate-500 hover:text-navy"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </div>
      {children}
    </Layout>
  );
}
