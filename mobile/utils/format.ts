export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "Unknown";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "Never";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Unknown";

  const diffSeconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (diffSeconds < 10) return "Just now";
  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function batteryLabel(battery: number | null | undefined): { label: string; level: "good" | "normal" | "low" | "critical" | "unknown" } {
  if (battery === null || battery === undefined) return { label: "Unknown", level: "unknown" };
  if (battery >= 60) return { label: "Good", level: "good" };
  if (battery >= 30) return { label: "Normal", level: "normal" };
  if (battery >= 15) return { label: "Low", level: "low" };
  return { label: "Critical", level: "critical" };
}
