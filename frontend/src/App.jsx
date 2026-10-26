import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import MyFiles from "./pages/MyFiles";
import FileDetails from "./pages/FileDetails";
import SharedWithMe from "./pages/SharedWithMe";
import AdminOverview from "./pages/AdminOverview";
import AdminUsers from "./pages/AdminUsers";
import AdminAuditLogs from "./pages/AdminAuditLogs";

export default function App() {
  const { user, loading } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <Register />} />

      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/files" element={<ProtectedRoute><MyFiles /></ProtectedRoute>} />
      <Route path="/files/:fileId" element={<ProtectedRoute><FileDetails /></ProtectedRoute>} />
      <Route path="/shared-with-me" element={<ProtectedRoute><SharedWithMe /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute adminOnly><AdminOverview /></ProtectedRoute>} />
      <Route path="/admin/users" element={<ProtectedRoute adminOnly><AdminUsers /></ProtectedRoute>} />
      <Route path="/admin/audit-logs" element={<ProtectedRoute adminOnly><AdminAuditLogs /></ProtectedRoute>} />

      <Route
        path="/"
        element={loading ? null : <Navigate to={user ? "/dashboard" : "/login"} replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
