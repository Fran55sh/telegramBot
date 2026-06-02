export type Category = {
  id: number;
  kind: string;
  slug: string;
  label: string;
  group_slug: string | null;
  group_label: string | null;
  is_active: boolean;
  is_system: boolean;
  sort_order: number;
};

export type CategoryGroup = {
  slug: string;
  label: string;
  categories: Category[];
};

export type Expense = {
  id: number;
  amount: string;
  category: string;
  category_label: string;
  date: string;
  description: string | null;
  created_at: string;
};

export type Income = {
  id: number;
  amount: string;
  category: string;
  category_label: string;
  source: string;
  date: string;
  description: string | null;
  created_at: string;
};

export type Reminder = {
  id: number;
  text: string;
  remind_at: string;
  amount: string | null;
  is_sent: boolean;
  sent_at: string | null;
  created_at: string;
};

export type Note = {
  id: number;
  text: string;
  tags: string[];
  created_at: string;
};

export type ActivityItem = {
  id: number;
  kind: string;
  title: string;
  subtitle: string;
  amount: string;
  date: string;
  created_at: string;
};

export type CategoryBreakdown = {
  slug: string;
  label: string;
  amount: string;
  percent: number;
};

export type Dashboard = {
  balance: string;
  total_incomes: string;
  total_expenses: string;
  expenses_by_category: CategoryBreakdown[];
  upcoming_reminders: Reminder[];
  recent_activity: ActivityItem[];
  pending_reminder_count: number;
};

export type Me = {
  chat_id: number;
  display_name: string;
  initials: string;
  pending_reminder_count: number;
};
