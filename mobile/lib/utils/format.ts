export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  try {
    const date = new Date(value);
    return date.toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return value;
  }
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  try {
    const date = new Date(value);
    return date.toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

const STATUS_LABEL_ID: Record<string, string> = {
  pending: "Menunggu",
  queued: "Antre",
  running: "Berjalan",
  completed: "Selesai",
  failed: "Gagal",
  cancelled: "Dibatalkan",
};

export function statusLabel(status: string): string {
  return STATUS_LABEL_ID[status] ?? status;
}

export function formatPercent(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}
