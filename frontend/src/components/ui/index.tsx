import type { ReactNode } from "react";
import { formatMoney } from "../../lib/format";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`glass-card p-6 ${className}`}>{children}</div>;
}

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const styles =
    variant === "primary"
      ? "bg-primary-container text-on-primary-container shadow-lg shadow-primary-container/20"
      : "glass-card text-on-surface hover:bg-surface-container-high/40";
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold transition active:scale-95 disabled:opacity-50 ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary focus:ring-1 focus:ring-primary"
      {...props}
    />
  );
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className="w-full resize-none rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary focus:ring-1 focus:ring-primary"
      {...props}
    />
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-on-surface-variant">{children}</label>;
}

export function Amount({ value, signed = false }: { value: string | number; signed?: boolean }) {
  const num = Number(value);
  const prefix = signed && num > 0 ? "+" : "";
  return <span className="font-mono tabular-nums">{prefix}{formatMoney(Math.abs(num))}</span>;
}

export function ModalSheet({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center bg-background/80 p-4 backdrop-blur-sm md:items-center">
      <div className="w-full max-w-md rounded-t-3xl border border-outline-variant/30 bg-surface-container-high p-6 shadow-2xl md:rounded-3xl">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-xl font-bold text-primary">{title}</h3>
          <button type="button" onClick={onClose} className="rounded-full p-2 text-on-surface-variant hover:bg-surface-variant">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Icon({ name, filled = false }: { name: string; filled?: boolean }) {
  return (
    <span
      className="material-symbols-outlined"
      style={filled ? { fontVariationSettings: "'FILL' 1" } : undefined}
    >
      {name}
    </span>
  );
}
