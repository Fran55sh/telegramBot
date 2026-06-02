import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useCreateReminder, useDeleteReminder, useReminders, useUpdateReminder } from "../api/hooks";
import { Header } from "../components/layout/AppShell";
import { Amount, Button, Card, Icon, Input, Label, ModalSheet } from "../components/ui";
import { formatDateTime, nowIsoLocal } from "../lib/format";

export function RemindersPage() {
  const [params, setParams] = useSearchParams();
  const [status, setStatus] = useState<"pending" | "sent">("pending");
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const { data = [] } = useReminders(status);
  const createReminder = useCreateReminder();
  const updateReminder = useUpdateReminder();
  const deleteReminder = useDeleteReminder();

  const [form, setForm] = useState({ text: "", remind_at: nowIsoLocal(), amount: "" });

  useEffect(() => {
    if (params.get("new") === "1") {
      setModalOpen(true);
      params.delete("new");
      setParams(params, { replace: true });
    }
  }, [params, setParams]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = {
      text: form.text,
      remind_at: new Date(form.remind_at).toISOString(),
      amount: form.amount ? Number(form.amount) : null,
    };
    if (editId) await updateReminder.mutateAsync({ id: editId, ...body });
    else await createReminder.mutateAsync(body);
    setModalOpen(false);
    setEditId(null);
    setForm({ text: "", remind_at: nowIsoLocal(), amount: "" });
  };

  return (
    <>
      <Header title="Recordatorios" />
      <main className="space-y-6 px-gutter py-6">
        <div className="flex rounded-full border border-outline-variant/20 bg-surface-container-low p-1">
          <button
            type="button"
            className={`flex-1 rounded-full py-2 text-xs font-semibold uppercase ${status === "pending" ? "bg-primary-container text-on-primary-container" : "text-on-surface-variant"}`}
            onClick={() => setStatus("pending")}
          >
            Pendientes
          </button>
          <button
            type="button"
            className={`flex-1 rounded-full py-2 text-xs font-semibold uppercase ${status === "sent" ? "bg-primary-container text-on-primary-container" : "text-on-surface-variant"}`}
            onClick={() => setStatus("sent")}
          >
            Historial
          </button>
        </div>

        <div className="space-y-3">
          {data.map((r) => (
            <Card key={r.id} className="flex items-start justify-between gap-3 p-4">
              <div>
                <p className={`font-medium ${r.is_sent ? "line-through opacity-60" : ""}`}>{r.text}</p>
                <p className="text-xs text-on-surface-variant">{formatDateTime(r.remind_at)}</p>
                {r.amount && <p className="mt-1"><Amount value={r.amount} /></p>}
              </div>
              <div className="flex gap-2">
                {!r.is_sent && (
                  <button
                    type="button"
                    className="text-primary"
                    onClick={() => {
                      setEditId(r.id);
                      setForm({
                        text: r.text,
                        remind_at: r.remind_at.slice(0, 16),
                        amount: r.amount ?? "",
                      });
                      setModalOpen(true);
                    }}
                  >
                    <Icon name="edit" />
                  </button>
                )}
                <button type="button" className="text-error" onClick={() => deleteReminder.mutate(r.id)}>
                  <Icon name="delete" />
                </button>
              </div>
            </Card>
          ))}
          {data.length === 0 && <p className="text-on-surface-variant">No hay recordatorios.</p>}
        </div>
      </main>

      <button
        type="button"
        onClick={() => {
          setEditId(null);
          setForm({ text: "", remind_at: nowIsoLocal(), amount: "" });
          setModalOpen(true);
        }}
        className="fixed bottom-24 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary-container to-secondary-container text-white shadow-lg"
      >
        <Icon name="add" />
      </button>

      <ModalSheet open={modalOpen} title={editId ? "Editar recordatorio" : "Nuevo recordatorio"} onClose={() => setModalOpen(false)}>
        <form className="space-y-4" onSubmit={submit}>
          <div>
            <Label>Qué necesitás recordar?</Label>
            <Input required value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} />
          </div>
          <div>
            <Label>Fecha y hora</Label>
            <Input type="datetime-local" required value={form.remind_at} onChange={(e) => setForm({ ...form, remind_at: e.target.value })} />
          </div>
          <div>
            <Label>Monto (opcional)</Label>
            <Input type="number" min="0.01" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          </div>
          <Button type="submit" className="w-full">Guardar</Button>
        </form>
      </ModalSheet>
    </>
  );
}
