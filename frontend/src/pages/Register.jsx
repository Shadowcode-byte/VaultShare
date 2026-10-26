import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Alert, Button } from "../components/ui";
import { AuthShell, Field } from "./Login";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(name, email, password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.detail || "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell>
      <h1 className="font-serif text-2xl font-bold text-navy">Create your account</h1>
      <p className="mt-1 text-sm text-slate-500">Register with your college email</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <Field label="Full name">
          <input
            type="text" required value={name} onChange={(e) => setName(e.target.value)}
            className="input" placeholder="Kamal Sharma"
          />
        </Field>
        <Field label="Email">
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="input" placeholder="you@upes.ac.in"
          />
        </Field>
        <Field label="Password">
          <input
            type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className="input" placeholder="At least 10 characters"
          />
          <span className="mt-1 block text-xs text-slate-400">
            Minimum 10 characters — length matters more than symbols or numbers.
          </span>
        </Field>

        <Alert>{error}</Alert>

        <Button type="submit" disabled={submitting} className="w-full justify-center">
          {submitting ? "Creating account…" : "Create account"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-navy hover:underline">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}
