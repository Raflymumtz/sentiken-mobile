import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";

export function LoadingState({ label = "Memuat data..." }: { label?: string }) {
  const { colors } = useThemeColors();
  return (
    <View style={styles.container} accessibilityRole="progressbar" accessibilityLabel={label}>
      <ActivityIndicator size="large" color={palette.primary} />
      <Text style={[styles.label, { color: colors.textMuted }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: "center", justifyContent: "center", padding: spacing.xl },
  label: { marginTop: spacing.sm, fontSize: 13 },
});
