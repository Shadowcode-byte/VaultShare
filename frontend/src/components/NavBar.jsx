import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/files", label: "My Files" },
  { to: "/shared-with-me", label: "Shared With Me" },
];

export default function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="bg-navy text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link to="/dashboard" className="flex items-center gap-2 font-serif text-xl font-bold">
          <ShieldIcon />
          VaultShare
        </Link>

        <div className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                location.pathname === l.to
                  ? "bg-white/15 text-white"
                  : "text-ice/80 hover:bg-white/10 hover:text-white"
              }`}
            >
              {l.label}
            </Link>
          ))}
          {user?.role === "admin" && (
            <Link
              to="/admin"
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                location.pathname.startsWith("/admin")
                  ? "bg-white/15 text-white"
                  : "text-ice/80 hover:bg-white/10 hover:text-white"
              }`}
            >
              Admin
            </Link>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-ice/80">{user?.name}</span>
          <button
            onClick={handleLogout}
            className="rounded-md border border-white/25 px-3 py-1.5 text-sm font-medium text-white hover:bg-white/10"
          >
            Log out
          </button>
        </div>
      </div>
    </nav>
  );
}

function ShieldIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
