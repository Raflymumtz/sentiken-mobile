import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";

import { Card } from "@/components/ui/Card";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";

const MENU = [
  { label: "Sumber Aplikasi", description: "Kelola PLN Mobile, MyPertamina, dan sumber lainnya", href: "/(tabs)/pengaturan/sumber-aplikasi" },
  { label: "Kamus Positif", description: "Kata dan bobot sentimen positif", href: "/(tabs)/pengaturan/kamus/positive" },
  { label: "Kamus Negatif", description: "Kata dan bobot sentimen negatif", href: "/(tabs)/pengaturan/kamus/negative" },
  { label: "Kamus Normalisasi", description: "Kata tidak baku → kata baku", href: "/(tabs)/pengaturan/kamus/normalization" },
  { label: "Kamus Stopword", description: "Kata yang diabaikan saat preprocessing", href: "/(tabs)/pengaturan/kamus/stopwords" },
  { label: "Akun", description: "Profil admin, tema, dan keluar", href: "/(tabs)/pengaturan/akun" },
] as const;

export default function PengaturanIndexScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();

  return (
    <ScreenContainer>
      {MENU.map((item) => (
        <Pressable
          key={item.href}
          onPress={() => router.push(item.href)}
          accessibilityRole="button"
          accessibilityLabel={item.label}
        >
          <Card>
            <Text style={[styles.label, { color: colors.text }]}>{item.label}</Text>
            <Text style={[styles.description, { color: colors.textMuted }]}>{item.description}</Text>
          </Card>
        </Pressable>
      ))}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 15, fontWeight: "700" },
  description: { fontSize: 12, marginTop: spacing.xs },
});
