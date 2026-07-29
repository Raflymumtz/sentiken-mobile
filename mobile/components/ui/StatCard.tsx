import { StyleSheet, Text, View } from "react-native";

import { Card } from "@/components/ui/Card";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";

interface StatCardProps {
  label: string;
  value: string | number;
  accentColor?: string;
  subtitle?: string;
}

export function StatCard({ label, value, accentColor = palette.primary, subtitle }: StatCardProps) {
  const { colors } = useThemeColors();
  return (
    <Card style={styles.card}>
      <View style={[styles.accent, { backgroundColor: accentColor }]} />
      <Text
        style={[styles.value, { color: colors.text }]}
        accessibilityRole="text"
        accessibilityLabel={`${label}: ${value}`}
      >
        {value}
      </Text>
      <Text style={[styles.label, { color: colors.textMuted }]}>{label}</Text>
      {subtitle ? <Text style={[styles.subtitle, { color: colors.textMuted }]}>{subtitle}</Text> : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { minWidth: 150, flexGrow: 1, flexBasis: "45%" },
  accent: { width: 32, height: 4, borderRadius: 2, marginBottom: spacing.sm },
  value: { fontSize: 24, fontWeight: "700" },
  label: { fontSize: 13, marginTop: 2 },
  subtitle: { fontSize: 11, marginTop: 2 },
});
