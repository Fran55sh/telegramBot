import { useState } from "react";
import { useCategories, useCreateCategory, useDeleteCategory, useUpdateCategory } from "../../api/hooks";
import { Button, Input, Label, ModalSheet } from "../ui";

export function CategoryManager({
  open,
  onClose,
  kind,
}: {
  open: boolean;
  onClose: () => void;
  kind: "expense" | "income";
}) {
  const { data = [] } = useCategories(kind);
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const deleteCategory = useDeleteCategory();
  const [label, setLabel] = useState("");
  const [groupLabel, setGroupLabel] = useState("Personalizado");

  const flat = data.flatMap((g) => g.categories);

  return (
    <ModalSheet open={open} title="Gestionar categorías" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <Label>Nueva categoría</Label>
          <div className="grid gap-2">
            <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Nombre" />
            <Input value={groupLabel} onChange={(e) => setGroupLabel(e.target.value)} placeholder="Grupo" />
            <Button
              type="button"
              disabled={!label.trim() || createCategory.isPending}
              onClick={async () => {
                await createCategory.mutateAsync({ kind, label, group_label: groupLabel });
                setLabel("");
              }}
            >
              Agregar
            </Button>
          </div>
        </div>
        <div className="max-h-64 space-y-2 overflow-y-auto">
          {flat.map((cat) => (
            <div key={cat.id} className="flex items-center gap-2 rounded-xl border border-outline-variant/20 p-3">
              <Input
                defaultValue={cat.label}
                onBlur={(e) => {
                  if (e.target.value !== cat.label) {
                    updateCategory.mutate({ id: cat.id, label: e.target.value } as { id: number; label: string });
                  }
                }}
              />
              {!cat.is_system && (
                <button
                  type="button"
                  className="text-error"
                  onClick={() => deleteCategory.mutate(cat.id)}
                >
                  <span className="material-symbols-outlined">delete</span>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </ModalSheet>
  );
}
