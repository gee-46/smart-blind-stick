/**
 * Design tokens for a serious assistive-technology app: high contrast,
 * large touch targets, and risk colors that are never the only signal
 * (always paired with text/icon per accessibility requirements).
 */
export const colors = {
  background: "#0B1F3A",
  surface: "#132A4D",
  surfaceElevated: "#1B3660",
  border: "#2C4D80",
  textPrimary: "#F5F8FC",
  textSecondary: "#B7C6E0",
  accent: "#4CA6FF",

  safe: "#2FB673",
  low: "#8CC63F",
  medium: "#F5A623",
  high: "#F2603C",
  critical: "#E0203A",

  online: "#2FB673",
  offline: "#6B7A99",
};

export const riskColor: Record<string, string> = {
  safe: colors.safe,
  low: colors.low,
  medium: colors.medium,
  high: colors.high,
  critical: colors.critical,
};

export const riskLabel: Record<string, string> = {
  safe: "SAFE",
  low: "LOW RISK",
  medium: "MEDIUM RISK",
  high: "HIGH RISK",
  critical: "CRITICAL",
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const radius = {
  sm: 8,
  md: 14,
  lg: 20,
};

export const typography = {
  h1: { fontSize: 30, fontWeight: "800" as const },
  h2: { fontSize: 22, fontWeight: "700" as const },
  h3: { fontSize: 18, fontWeight: "700" as const },
  body: { fontSize: 16, fontWeight: "400" as const },
  bodyBold: { fontSize: 16, fontWeight: "700" as const },
  caption: { fontSize: 13, fontWeight: "500" as const },
};

export const minTouchTarget = 48;
