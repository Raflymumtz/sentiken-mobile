import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, radius, spacing } from "@/lib/theme";

interface PrimaryButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  loading?: boolean;
  accessibilityLabel?: string;
}

export function PrimaryButton({
  label,
  onPress,
  variant = "primary",
  disabled = false,
  loading = false,
  accessibilityLabel,
}: PrimaryButtonProps) {
  const { colors } = useThemeColors();
  const isDisabled = disabled || loading;

  const backgroundColor =
    variant === "primary"
      ? palette.primary
      : variant === "danger"
        ? palette.negative
        : colors.surface;
  const textColor = variant === "secondary" ? colors.text : "#FFFFFF";
  const borderColor = variant === "secondary" ? colors.border : "transparent";

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor, borderColor, opacity: isDisabled ? 0.6 : pressed ? 0.85 : 1 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text style={[styles.label, { color: textColor }]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    borderRadius: radius.sm,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  label: { fontSize: 15, fontWeight: "600" },
});
