export const palette = {
  primary: "#1D4ED8",
  primaryDark: "#3B82F6",
  positive: "#16A34A",
  negative: "#DC2626",
  neutral: "#CA8A04",
  light: {
    background: "#F5F7FB",
    surface: "#FFFFFF",
    text: "#111827",
    textMuted: "#6B7280",
    border: "#E5E7EB",
    danger: "#DC2626",
  },
  dark: {
    background: "#0B1120",
    surface: "#111827",
    text: "#F3F4F6",
    textMuted: "#9CA3AF",
    border: "#1F2937",
    danger: "#F87171",
  },
};

export type ThemeColors = typeof palette.light;

export function getThemeColors(scheme: "light" | "dark" | null | undefined): ThemeColors {
  return scheme === "dark" ? palette.dark : palette.light;
}

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const radius = {
  sm: 6,
  md: 12,
  lg: 16,
};

export function labelColor(label: string): string {
  if (label === "positive") return palette.positive;
  if (label === "negative") return palette.negative;
  return palette.neutral;
}

export function labelText(label: string): string {
  if (label === "positive") return "Positif";
  if (label === "negative") return "Negatif";
  return "Netral";
}
