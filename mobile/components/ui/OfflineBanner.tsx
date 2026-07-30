import { Pressable, StyleSheet, Text, View } from "react-native";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";

interface OfflineBannerProps {
  onRetry: () => void;
}

/** Ditampilkan di atas layar saat backend tidak bisa dihubungi -- data yang
 * terlihat adalah data tersimpan dari sesi terakhir kali aplikasi berhasil
 * terhubung, bukan data terbaru. */
export function OfflineBanner({ onRetry }: OfflineBannerProps) {
  const { colors } = useThemeColors();
  return (
    <View style={[styles.container, { backgroundColor: palette.negative, borderBottomColor: colors.border }]}>
      <Text style={styles.text}>Mode offline — menampilkan data tersimpan, bukan data terbaru.</Text>
      <Pressable onPress={onRetry} hitSlop={8} accessibilityRole="button" accessibilityLabel="Coba hubungkan lagi">
        <Text style={styles.retry}>Coba Lagi</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  text: { color: "#fff", fontSize: 11, flex: 1, marginRight: spacing.sm },
  retry: { color: "#fff", fontSize: 11, fontWeight: "700", textDecorationLine: "underline" },
});
