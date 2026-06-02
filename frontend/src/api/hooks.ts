import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type {
  CategoryGroup,
  Dashboard,
  Expense,
  Income,
  Me,
  Note,
  Reminder,
} from "./types";

export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: () => apiFetch<Me>("/api/me") });
}

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<Dashboard>("/api/reports/dashboard"),
  });
}

export function useCategories(kind: "expense" | "income") {
  return useQuery({
    queryKey: ["categories", kind],
    queryFn: () => apiFetch<CategoryGroup[]>(`/api/categories?kind=${kind}`),
  });
}

export function useExpenses(params?: { q?: string; category?: string }) {
  const search = new URLSearchParams();
  if (params?.q) search.set("q", params.q);
  if (params?.category) search.set("category", params.category);
  const qs = search.toString();
  return useQuery({
    queryKey: ["expenses", params],
    queryFn: () => apiFetch<Expense[]>(`/api/expenses${qs ? `?${qs}` : ""}`),
  });
}

export function useIncomes(params?: { q?: string; category?: string }) {
  const search = new URLSearchParams();
  if (params?.q) search.set("q", params.q);
  if (params?.category) search.set("category", params.category);
  const qs = search.toString();
  return useQuery({
    queryKey: ["incomes", params],
    queryFn: () => apiFetch<Income[]>(`/api/incomes${qs ? `?${qs}` : ""}`),
  });
}

export function useReminders(status: "pending" | "sent" | "all") {
  return useQuery({
    queryKey: ["reminders", status],
    queryFn: () => apiFetch<Reminder[]>(`/api/reminders?status=${status}`),
  });
}

export function useNotes(q?: string) {
  const qs = q ? `?q=${encodeURIComponent(q)}` : "";
  return useQuery({
    queryKey: ["notes", q],
    queryFn: () => apiFetch<Note[]>(`/api/notes${qs}`),
  });
}

function invalidateFinance(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["dashboard"] });
  qc.invalidateQueries({ queryKey: ["expenses"] });
  qc.invalidateQueries({ queryKey: ["incomes"] });
}

export function useCreateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => apiFetch<Expense>("/api/expenses", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => invalidateFinance(qc),
  });
}

export function useUpdateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number } & object) =>
      apiFetch<Expense>(`/api/expenses/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => invalidateFinance(qc),
  });
}

export function useDeleteExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/api/expenses/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateFinance(qc),
  });
}

export function useCreateIncome() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => apiFetch<Income>("/api/incomes", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => invalidateFinance(qc),
  });
}

export function useUpdateIncome() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number } & object) =>
      apiFetch<Income>(`/api/incomes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => invalidateFinance(qc),
  });
}

export function useDeleteIncome() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/api/incomes/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateFinance(qc),
  });
}

export function useCreateReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) =>
      apiFetch<Reminder>("/api/reminders", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reminders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useUpdateReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number } & object) =>
      apiFetch<Reminder>(`/api/reminders/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reminders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useDeleteReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/api/reminders/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reminders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useCreateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => apiFetch<Note>("/api/notes", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useUpdateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number } & object) =>
      apiFetch<Note>(`/api/notes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useDeleteNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/api/notes/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) =>
      apiFetch("/api/categories", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useUpdateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number } & object) =>
      apiFetch(`/api/categories/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useDeleteCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/api/categories/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}
