import NavBar from "./NavBar";

export default function Layout({ title, subtitle, actions, children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar />
      <div className="mx-auto max-w-6xl px-6 py-8">
        {(title || actions) && (
          <div className="mb-6 flex items-start justify-between">
            <div>
              {title && <h1 className="font-serif text-2xl font-bold text-navy">{title}</h1>}
              {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
            </div>
            {actions && <div className="flex gap-2">{actions}</div>}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
