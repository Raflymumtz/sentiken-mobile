import { useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useCurrentUser, useLogout } from "@/lib/hooks/useAuth";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useSettingsStore, type ThemePreference } from "@/lib/store/settingsStore";
import { spacing } from "@/lib/theme";

const THEME_OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "system", label: "Ikuti Sistem" },
  { value: "light", label: "Terang" },
  { value: "dark", label: "Gelap" },
];

export default function AkunScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();
  const userQuery = useCurrentUser();
  const logoutMutation = useLogout();
  const { themePreference, setThemePreference } = useSettingsStore();
  const [confirmLogout, setConfirmLogout] = useState(false);

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    setConfirmLogout(false);
    router.replace("/(auth)/login");
  };

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Profil</Text>
        <Text style={[styles.meta, { color: colors.textMuted }]}>
          {userQuery.data?.full_name ?? "-"}
        </Text>
        <Text style={[styles.meta, { color: colors.textMuted }]}>{userQuery.data?.email ?? "-"}</Text>
      </Card>

      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Tampilan</Text>
        <View style={styles.themeRow}>
          {THEME_OPTIONS.map((opt) => (
            <PrimaryButton
              key={opt.value}
              label={opt.label}
              onPress={() => setThemePreference(opt.value)}
              variant={themePreference === opt.value ? "primary" : "secondary"}
            />
          ))}
        </View>
      </Card>

      <PrimaryButton label="Keluar" onPress={() => setConfirmLogout(true)} variant="danger" />

      <ConfirmDialog
        visible={confirmLogout}
        title="Keluar dari aplikasi?"
        description="Anda perlu login kembali untuk mengakses aplikasi."
        confirmLabel="Keluar"
        destructive
        onConfirm={handleLogout}
        onCancel={() => setConfirmLogout(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  meta: { fontSize: 13, marginTop: 2 },
  themeRow: { flexDirection: "row", gap: spacing.sm, flexWrap: "wrap" },
});
