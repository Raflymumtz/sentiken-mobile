import { Modal, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";

interface ConfirmDialogProps {
  visible: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  visible,
  title,
  description,
  confirmLabel = "Konfirmasi",
  cancelLabel = "Batal",
  destructive = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const { colors } = useThemeColors();
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <View style={styles.overlay}>
        <View style={[styles.dialog, { backgroundColor: colors.surface }]}>
          <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
          {description ? (
            <Text style={[styles.description, { color: colors.textMuted }]}>{description}</Text>
          ) : null}
          <View style={styles.actions}>
            <View style={styles.actionButton}>
              <PrimaryButton label={cancelLabel} onPress={onCancel} variant="secondary" />
            </View>
            <View style={styles.actionButton}>
              <PrimaryButton
                label={confirmLabel}
                onPress={onConfirm}
                variant={destructive ? "danger" : "primary"}
              />
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  dialog: { width: "100%", maxWidth: 400, borderRadius: 16, padding: spacing.lg },
  title: { fontSize: 17, fontWeight: "700", marginBottom: spacing.xs },
  description: { fontSize: 14, marginBottom: spacing.md },
  actions: { flexDirection: "row", gap: spacing.sm },
  actionButton: { flex: 1 },
});
