import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAuthConfig, isAuthConfigured, setAuthConfig } from "../../api/client";
import { Button, Input, Label, ModalSheet } from "../ui";

export function AuthSetupModal({ forceOpen = false }: { forceOpen?: boolean }) {
  const qc = useQueryClient();
  const current = getAuthConfig();
  const [open, setOpen] = useState(forceOpen || !isAuthConfigured());
  const [token, setToken] = useState(current.token);
  const [chatId, setChatId] = useState(current.chatId);

  const save = () => {
    if (!token.trim() || !/^\d+$/.test(chatId.trim())) {
      return;
    }
    setAuthConfig(token, chatId);
    setOpen(false);
    qc.invalidateQueries();
  };

  if (!open) return null;

  return (
    <ModalSheet
      open={open}
      title="Conectar con Telegram"
      onClose={() => {
        if (isAuthConfigured()) setOpen(false);
      }}
    >
      <p className="mb-4 text-sm text-on-surface-variant">
        La web muestra datos del mismo usuario que el bot. Usá tu <strong>chat_id</strong> numérico
        (no el token del bot). Lo ves en logs del servidor:{" "}
        <code className="text-primary">telegram_message chat_id=...</code>
      </p>
      <div className="space-y-4">
        <div>
          <Label>WEB_APP_TOKEN</Label>
          <Input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Mismo valor que WEB_APP_TOKEN en el servidor"
          />
        </div>
        <div>
          <Label>Telegram chat_id</Label>
          <Input
            inputMode="numeric"
            value={chatId}
            onChange={(e) => setChatId(e.target.value.replace(/\D/g, ""))}
            placeholder="Ej: 123456789"
          />
        </div>
        <Button type="button" className="w-full" onClick={save} disabled={!token.trim() || !/^\d+$/.test(chatId.trim())}>
          Guardar y conectar
        </Button>
      </div>
    </ModalSheet>
  );
}

export function SettingsModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const current = getAuthConfig();
  const [token, setToken] = useState(current.token);
  const [chatId, setChatId] = useState(current.chatId);

  const save = () => {
    if (!token.trim() || !/^\d+$/.test(chatId.trim())) return;
    setAuthConfig(token, chatId);
    qc.invalidateQueries();
    onClose();
  };

  return (
    <ModalSheet open={open} title="Ajustes de conexión" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <Label>WEB_APP_TOKEN</Label>
          <Input type="password" value={token} onChange={(e) => setToken(e.target.value)} />
        </div>
        <div>
          <Label>Telegram chat_id</Label>
          <Input
            inputMode="numeric"
            value={chatId}
            onChange={(e) => setChatId(e.target.value.replace(/\D/g, ""))}
          />
        </div>
        <p className="text-xs text-on-surface-variant">
          Chat id actual en uso: {current.chatId || "(no configurado)"}
        </p>
        <Button type="button" className="w-full" onClick={save}>
          Guardar
        </Button>
      </div>
    </ModalSheet>
  );
}
