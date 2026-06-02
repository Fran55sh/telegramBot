import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  useCategories,
  useCreateExpense,
  useCreateIncome,
  useDeleteExpense,
  useDeleteIncome,
  useExpenses,
  useIncomes,
  useUpdateExpense,
  useUpdateIncome,
} from "../api/hooks";
import { CategoryManager } from "../components/categories/CategoryManager";
import { CategorySelect } from "../components/categories/CategorySelect";
import { Header } from "../components/layout/AppShell";
import { Amount, Button, Card, Icon, Input, Label, ModalSheet, Textarea } from "../components/ui";
import { formatDate, todayIso } from "../lib/format";

type Tab = "expense" | "income";

export function FinancePage() {
  const [params, setParams] = useSearchParams();
  const [tab, setTab] = useState<Tab>((params.get("tab") as Tab) || "expense");
  const [q, setQ] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [categoryModal, setCategoryModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);

  const expenseQuery = useExpenses({ q });
  const incomeQuery = useIncomes({ q });
  const expenseCategories = useCategories("expense");
  const incomeCategories = useCategories("income");

  const createExpense = useCreateExpense();
  const updateExpense = useUpdateExpense();
  const deleteExpense = useDeleteExpense();
  const createIncome = useCreateIncome();
  const updateIncome = useUpdateIncome();
  const deleteIncome = useDeleteIncome();

  const defaultCategory = useMemo(() => {
    const groups = tab === "expense" ? expenseCategories.data : incomeCategories.data;
    return groups?.[0]?.categories[0]?.slug ?? (tab === "expense" ? "sin-clasificar" : "otros-ingresos");
  }, [tab, expenseCategories.data, incomeCategories.data]);

  const [form, setForm] = useState({
    amount: "",
    category: defaultCategory,
    source: "",
    date: todayIso(),
    description: "",
  });

  useEffect(() => {
    setForm((f) => ({ ...f, category: defaultCategory }));
  }, [defaultCategory, tab]);

  useEffect(() => {
    const kind = params.get("new");
    if (kind === "expense" || kind === "income") {
      setTab(kind);
      setModalOpen(true);
      params.delete("new");
      setParams(params, { replace: true });
    }
  }, [params, setParams]);

  const rows = tab === "expense" ? expenseQuery.data ?? [] : incomeQuery.data ?? [];

  const openCreate = () => {
    setEditId(null);
    setForm({ amount: "", category: defaultCategory, source: "", date: todayIso(), description: "" });
    setModalOpen(true);
  };

  const openEdit = (row: (typeof rows)[number]) => {
    setEditId(row.id);
    setForm({
      amount: String(row.amount),
      category: row.category,
      source: tab === "income" && "source" in row ? String(row.source) : "",
      date: row.date,
      description: row.description ?? "",
    });
    setModalOpen(true);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = {
      amount: Number(form.amount),
      category: form.category,
      date: form.date,
      description: form.description || null,
      ...(tab === "income" ? { source: form.source || form.category } : {}),
    };
    if (editId) {
      if (tab === "expense") await updateExpense.mutateAsync({ id: editId, ...body });
      else await updateIncome.mutateAsync({ id: editId, ...body });
    } else {
      if (tab === "expense") await createExpense.mutateAsync(body);
      else await createIncome.mutateAsync(body);
    }
    setModalOpen(false);
  };

  return (
    <>
      <Header title="Finanzas" />
      <main className="space-y-6 px-gutter py-6">
        <Card>
          <p className="text-xs uppercase tracking-wider text-on-surface-variant">Resumen rápido</p>
          <p className="mt-2 text-sm text-on-surface-variant">Gestioná gastos e ingresos con categorías del catálogo.</p>
          <Button type="button" variant="ghost" className="mt-4" onClick={() => setCategoryModal(true)}>
            Gestionar categorías
          </Button>
        </Card>

        <div className="flex gap-2">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar movimientos..." />
        </div>

        <div className="flex rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-1">
          <button
            type="button"
            className={`flex-1 rounded-lg py-2 text-xs font-semibold uppercase ${tab === "expense" ? "bg-primary-container text-on-primary-container" : "text-on-surface-variant"}`}
            onClick={() => setTab("expense")}
          >
            Gastos
          </button>
          <button
            type="button"
            className={`flex-1 rounded-lg py-2 text-xs font-semibold uppercase ${tab === "income" ? "bg-primary-container text-on-primary-container" : "text-on-surface-variant"}`}
            onClick={() => setTab("income")}
          >
            Ingresos
          </button>
        </div>

        <div className="space-y-3">
          {rows.map((row) => (
            <Card key={row.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{row.description || row.category_label}</p>
                <p className="text-xs text-on-surface-variant">
                  {row.category_label} • {formatDate(row.date)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Amount value={tab === "expense" ? `-${row.amount}` : row.amount} signed />
                <button type="button" onClick={() => openEdit(row)} className="text-primary"><Icon name="edit" /></button>
                <button
                  type="button"
                  onClick={() => (tab === "expense" ? deleteExpense.mutate(row.id) : deleteIncome.mutate(row.id))}
                  className="text-error"
                >
                  <Icon name="delete" />
                </button>
              </div>
            </Card>
          ))}
          {rows.length === 0 && <p className="text-on-surface-variant">No hay movimientos.</p>}
        </div>
      </main>

      <button
        type="button"
        onClick={openCreate}
        className="fixed bottom-24 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-primary-container text-on-primary-container shadow-lg"
      >
        <Icon name="add" />
      </button>

      <ModalSheet open={modalOpen} title={editId ? "Editar movimiento" : "Nuevo movimiento"} onClose={() => setModalOpen(false)}>
        <form className="space-y-4" onSubmit={submit}>
          <div>
            <Label>Monto (ARS)</Label>
            <Input type="number" min="0.01" step="0.01" required value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          </div>
          <CategorySelect kind={tab} value={form.category} onChange={(category) => setForm({ ...form, category })} />
          {tab === "income" && (
            <div>
              <Label>Origen (opcional)</Label>
              <Input value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} placeholder="Detalle del ingreso" />
            </div>
          )}
          <div>
            <Label>Fecha</Label>
            <Input type="date" required value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
          </div>
          <div>
            <Label>Descripción</Label>
            <Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <Button type="submit" className="w-full">Guardar</Button>
        </form>
      </ModalSheet>

      <CategoryManager open={categoryModal} onClose={() => setCategoryModal(false)} kind={tab} />
    </>
  );
}
