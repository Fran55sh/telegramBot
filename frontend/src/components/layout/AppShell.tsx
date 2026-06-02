import { NavLink, Outlet } from "react-router-dom";
import { useMe } from "../../api/hooks";
import { Icon } from "../ui";

const links = [
  { to: "/", label: "Dashboard", icon: "dashboard" },
  { to: "/finanzas", label: "Finanzas", icon: "account_balance_wallet" },
  { to: "/recordatorios", label: "Recordatorios", icon: "event_upcoming" },
  { to: "/notas", label: "Notas", icon: "description" },
];

export function Header({ title }: { title: string }) {
  const { data: me } = useMe();
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-outline-variant/20 bg-surface/80 px-gutter backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/20 bg-primary-container/30 text-sm font-bold text-primary">
          {me?.initials ?? "??"}
        </div>
        <h1 className="text-2xl font-bold text-primary">{title}</h1>
      </div>
      <button type="button" className="relative rounded-full p-2 text-on-surface-variant hover:bg-surface-container-high/40">
        <Icon name="notifications" />
        {(me?.pending_reminder_count ?? 0) > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-error px-1 text-[10px] font-bold text-surface">
            {me?.pending_reminder_count}
          </span>
        )}
      </button>
    </header>
  );
}

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 z-50 flex w-full justify-around rounded-t-xl border-t border-outline-variant/20 bg-surface-container/60 px-4 pb-4 pt-2 backdrop-blur-xl">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.to === "/"}
          className={({ isActive }) =>
            `flex flex-col items-center justify-center px-4 py-1 text-xs font-semibold uppercase tracking-wide transition ${
              isActive ? "rounded-full bg-primary-container text-on-primary-container" : "text-on-surface-variant hover:text-primary"
            }`
          }
        >
          <Icon name={link.icon} />
          <span>{link.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export function AppShell() {
  return (
    <div className="mx-auto min-h-screen max-w-[1200px] pb-28">
      <Outlet />
      <BottomNav />
    </div>
  );
}
