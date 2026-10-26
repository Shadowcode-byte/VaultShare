export function Alert({ kind = "error", children }) {
  const styles = {
    error: "bg-red-50 text-red-700 border-red-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    info: "bg-ice-light text-navy border-ice",
  };
  if (!children) return null;
  return <div className={`rounded-md border px-4 py-2.5 text-sm ${styles[kind]}`}>{children}</div>;
}

export function Badge({ children, tone = "navy" }) {
  const styles = {
    navy: "bg-navy text-white",
    ice: "bg-ice-light text-navy",
    gray: "bg-slate-100 text-slate-600",
    red: "bg-red-50 text-red-600",
    green: "bg-emerald-50 text-emerald-700",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[tone]}`}>
      {children}
    </span>
  );
}

export function Button({ children, variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-navy text-white hover:bg-navy-light disabled:opacity-50",
    secondary: "border border-navy/20 text-navy hover:bg-ice-light disabled:opacity-50",
    danger: "border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50",
  };
  return (
    <button
      className={`rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white py-16 text-center">
      <p className="font-medium text-slate-700">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Spinner() {
  return (
    <div className="flex justify-center py-10">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
    </div>
  );
}
