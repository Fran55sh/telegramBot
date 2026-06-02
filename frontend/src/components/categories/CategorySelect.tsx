import { useCategories } from "../../api/hooks";
import type { CategoryGroup } from "../../api/types";
import { Label } from "../ui";

export function CategorySelect({
  kind,
  value,
  onChange,
}: {
  kind: "expense" | "income";
  value: string;
  onChange: (slug: string) => void;
}) {
  const { data = [] } = useCategories(kind);
  return (
    <div>
      <Label>Categoría</Label>
      <select
        className="w-full rounded-xl border border-outline-variant bg-surface px-4 py-3 text-sm outline-none focus:border-primary"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {data.map((group: CategoryGroup) => (
          <optgroup key={group.slug} label={group.label}>
            {group.categories.map((cat) => (
              <option key={cat.id} value={cat.slug}>
                {cat.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </div>
  );
}
