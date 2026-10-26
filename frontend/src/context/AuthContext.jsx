import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true while we check for an existing session on first load

  const refresh = useCallback(async () => {
    try {
      const me = await api.me();
      setUser(me);
    } catch {
      // No valid session (or it expired/was revoked elsewhere) — this
      // is the normal, expected path for a first-time visitor, not an
      // error worth surfacing.
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email, password) => {
    const me = await api.login(email, password);
    setUser(me);
  };

  const register = async (name, email, password) => {
    await api.register(name, email, password);
    // Registration does not log the user in automatically (no session
    // cookie is set by /auth/register) — the backend design keeps
    // "create an account" and "start a session" as two separate,
    // explicit steps. So we log in right after, using the same
    // credentials the user just chose.
    await login(email, password);
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
