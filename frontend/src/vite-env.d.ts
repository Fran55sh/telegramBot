/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WEB_APP_TOKEN?: string;
  readonly VITE_TELEGRAM_CHAT_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
