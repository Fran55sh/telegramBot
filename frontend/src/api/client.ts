const TOKEN_KEY = "web_app_token";
const CHAT_ID_KEY = "telegram_chat_id";

export function getAuthConfig() {
  return {
    token: localStorage.getItem(TOKEN_KEY) ?? import.meta.env.VITE_WEB_APP_TOKEN ?? "dev-token-change-me",
    chatId: localStorage.getItem(CHAT_ID_KEY) ?? import.meta.env.VITE_TELEGRAM_CHAT_ID ?? "1",
  };
}

export function setAuthConfig(token: string, chatId: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(CHAT_ID_KEY, chatId);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { token, chatId } = getAuthConfig();
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Telegram-Chat-Id": chatId,
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || response.statusText);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
