import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useCreateNote, useDeleteNote, useNotes, useUpdateNote } from "../api/hooks";
import { Header } from "../components/layout/AppShell";
import { Button, Card, Icon, Input, Label, ModalSheet, Textarea } from "../components/ui";

export function NotesPage() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const [tag, setTag] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const { data = [] } = useNotes(q);
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();

  const [form, setForm] = useState({ text: "", tags: "" });

  useEffect(() => {
    if (params.get("new") === "1") {
      setModalOpen(true);
      params.delete("new");
      setParams(params, { replace: true });
    }
  }, [params, setParams]);

  const tags = useMemo(() => {
    const all = new Set<string>();
    data.forEach((n) => n.tags.forEach((t) => all.add(t)));
    return ["Todas", ...Array.from(all)];
  }, [data]);

  const filtered = tag && tag !== "Todas" ? data.filter((n) => n.tags.includes(tag)) : data;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const tagsList = form.tags.split(",").map((t) => t.trim()).filter(Boolean);
    const body = { text: form.text, tags: tagsList };
    if (editId) await updateNote.mutateAsync({ id: editId, ...body });
    else await createNote.mutateAsync(body);
    setModalOpen(false);
    setEditId(null);
    setForm({ text: "", tags: "" });
  };

  return (
    <>
      <Header title="Notas" />
      <main className="space-y-6 px-gutter py-6">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar ideas, gastos o planes..." />

        <div className="-mx-gutter flex gap-2 overflow-x-auto px-gutter pb-2">
          {tags.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTag(t === "Todas" ? null : t)}
              className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-semibold uppercase ${
                (t === "Todas" && !tag) || tag === t
                  ? "bg-primary-container text-on-primary-container"
                  : "bg-surface-container-high text-on-surface-variant"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((note) => (
            <Card key={note.id} className="flex flex-col gap-3">
              <p className="line-clamp-4 text-on-surface-variant">{note.text}</p>
              <div className="flex flex-wrap gap-2">
                {note.tags.map((t) => (
                  <span key={t} className="rounded-lg bg-surface-variant px-2 py-1 text-xs uppercase">{t}</span>
                ))}
              </div>
              <div className="mt-auto flex gap-2">
                <button
                  type="button"
                  className="text-primary"
                  onClick={() => {
                    setEditId(note.id);
                    setForm({ text: note.text, tags: note.tags.join(", ") });
                    setModalOpen(true);
                  }}
                >
                  <Icon name="edit" />
                </button>
                <button type="button" className="text-error" onClick={() => deleteNote.mutate(note.id)}>
                  <Icon name="delete" />
                </button>
              </div>
            </Card>
          ))}
          {filtered.length === 0 && <p className="text-on-surface-variant">No hay notas.</p>}
        </div>
      </main>

      <button
        type="button"
        onClick={() => {
          setEditId(null);
          setForm({ text: "", tags: "" });
          setModalOpen(true);
        }}
        className="fixed bottom-24 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-container text-on-primary-container shadow-lg"
      >
        <Icon name="add" />
      </button>

      <ModalSheet open={modalOpen} title={editId ? "Editar nota" : "Nueva nota"} onClose={() => setModalOpen(false)}>
        <form className="space-y-4" onSubmit={submit}>
          <div>
            <Label>Texto</Label>
            <Textarea rows={4} required value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} />
          </div>
          <div>
            <Label>Tags (separados por coma)</Label>
            <Input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="inversiones, urgente" />
          </div>
          <Button type="submit" className="w-full">Guardar</Button>
        </form>
      </ModalSheet>
    </>
  );
}
