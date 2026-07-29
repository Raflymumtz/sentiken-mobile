import { StyleSheet, Text, TextInput, View, type KeyboardTypeOptions } from "react-native";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { radius, spacing } from "@/lib/theme";

interface TextFieldProps {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  onBlur?: () => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  error?: string;
  keyboardType?: KeyboardTypeOptions;
  multiline?: boolean;
  autoCapitalize?: "none" | "sentences" | "words" | "characters";
}

export function TextField({
  label,
  value,
  onChangeText,
  onBlur,
  placeholder,
  secureTextEntry,
  error,
  keyboardType,
  multiline,
  autoCapitalize = "sentences",
}: TextFieldProps) {
  const { colors } = useThemeColors();
  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: colors.text }]}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        onBlur={onBlur}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        secureTextEntry={secureTextEntry}
        keyboardType={keyboardType}
        multiline={multiline}
        autoCapitalize={autoCapitalize}
        accessibilityLabel={label}
        style={[
          styles.input,
          multiline && styles.multiline,
          { color: colors.text, borderColor: error ? "#DC2626" : colors.border, backgroundColor: colors.surface },
        ]}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: spacing.md },
  label: { fontSize: 13, fontWeight: "600", marginBottom: spacing.xs },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    fontSize: 15,
  },
  multiline: { minHeight: 96, textAlignVertical: "top", paddingTop: spacing.sm },
  error: { color: "#DC2626", fontSize: 12, marginTop: spacing.xs },
});
