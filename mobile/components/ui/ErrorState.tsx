import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = "Terjadi kesalahan. Silakan coba lagi.", onRetry }: ErrorStateProps) {
  const { colors } = useThemeColors();
  return (
    <View style={styles.container} accessibilityRole="alert">
      <Text style={[styles.message, { color: colors.danger }]}>{message}</Text>
      {onRetry ? (
        <View style={styles.action}>
          <PrimaryButton label="Coba Lagi" onPress={onRetry} variant="secondary" />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: "center", justifyContent: "center", padding: spacing.xl },
  message: { fontSize: 14, textAlign: "center", fontWeight: "500" },
  action: { marginTop: spacing.md },
});
