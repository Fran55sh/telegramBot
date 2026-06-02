import { useState } from "react";
import { Link } from "react-router-dom";
import { useDashboard } from "../api/hooks";
import { Header } from "../components/layout/AppShell";
import { Amount, Button, Card, Icon } from "../components/ui";
import { formatDateTime, formatMoney } from "../lib/format";

export function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const [hideBalance, setHideBalance] = useState(false);

  if (isLoading || !data) {
    return (
      <>
        <Header title="Hoy" />
        <main className="px-gutter py-6 text-on-surface-variant">Cargando...</main>
      </>
    );
  }

  return (
    <>
      <Header title="Hoy" />
      <main className="space-y-8 px-gutter py-6">
        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 -z-10 bg-gradient-to-br from-primary-container/20 to-secondary-container/20 blur-3xl" />
          <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Balance del mes</p>
          <button type="button" onClick={() => setHideBalance((v) => !v)} className="mt-2 block text-left">
            <p className={`font-mono text-3xl tabular-nums ${hideBalance ? "blur-md" : ""}`}>
              {formatMoney(data.balance)}
            </p>
          </button>
          <div className="mt-4 flex gap-4 text-sm">
            <span className="text-tertiary">Ingresos {formatMoney(data.total_incomes)}</span>
            <span className="text-error">Egresos {formatMoney(data.total_expenses)}</span>
          </div>
        </Card>

        <section>
          <h2 className="mb-4 text-lg font-semibold">Acciones rápidas</h2>
          <div className="flex gap-3 overflow-x-auto pb-2">
            <Link to="/finanzas?new=expense"><Button><Icon name="add_circle" />Nuevo Gasto</Button></Link>
            <Link to="/finanzas?new=income"><Button variant="ghost"><Icon name="payments" />Ingreso</Button></Link>
            <Link to="/recordatorios?new=1"><Button variant="ghost"><Icon name="event" />Recordatorio</Button></Link>
            <Link to="/notas?new=1"><Button variant="ghost"><Icon name="description" />Nota</Button></Link>
          </div>
        </section>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
          <Card className="md:col-span-7">
            <h2 className="mb-4 text-lg font-semibold">Gastos por categoría</h2>
            <div className="space-y-3">
              {data.expenses_by_category.map((item) => (
                <div key={item.slug} className="flex items-center justify-between text-sm">
                  <span>{item.label}</span>
                  <span className="font-mono tabular-nums">{formatMoney(item.amount)} ({item.percent}%)</span>
                </div>
              ))}
              {data.expenses_by_category.length === 0 && (
                <p className="text-on-surface-variant">Sin gastos este mes.</p>
              )}
            </div>
          </Card>

          <Card className="md:col-span-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recordatorios</h2>
              {data.pending_reminder_count > 0 && (
                <span className="rounded-full bg-error/20 px-2 py-0.5 text-xs font-bold text-error">
                  {data.pending_reminder_count} pendientes
                </span>
              )}
            </div>
            <div className="space-y-3">
              {data.upcoming_reminders.map((r) => (
                <div key={r.id} className="rounded-xl border border-outline-variant/10 bg-surface-container-low p-3">
                  <p className="font-medium">{r.text}</p>
                  <p className="text-xs text-on-surface-variant">{formatDateTime(r.remind_at)}</p>
                  {r.amount && <p className="mt-1 font-mono text-sm tabular-nums">{formatMoney(r.amount)}</p>}
                </div>
              ))}
              {data.upcoming_reminders.length === 0 && (
                <p className="text-on-surface-variant">No hay recordatorios próximos.</p>
              )}
            </div>
          </Card>
        </div>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Actividad reciente</h2>
            <Link to="/finanzas" className="text-sm text-primary">Ver todo</Link>
          </div>
          <Card className="divide-y divide-outline-variant/10 p-0">
            {data.recent_activity.map((item) => (
              <div key={`${item.kind}-${item.id}`} className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium">{item.title}</p>
                  <p className="text-xs text-on-surface-variant">{item.subtitle}</p>
                </div>
                <Amount value={item.amount} signed />
              </div>
            ))}
            {data.recent_activity.length === 0 && (
              <p className="p-4 text-on-surface-variant">Sin movimientos recientes.</p>
            )}
          </Card>
        </section>
      </main>
    </>
  );
}
