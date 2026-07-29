import { Stack } from "expo-router";

export default function PengaturanLayout() {
  return (
    <Stack screenOptions={{ headerTitleAlign: "center" }}>
      <Stack.Screen name="index" options={{ title: "Pengaturan" }} />
      <Stack.Screen name="sumber-aplikasi/index" options={{ title: "Sumber Aplikasi" }} />
      <Stack.Screen name="kamus/[type]" options={{ title: "Kamus" }} />
      <Stack.Screen name="akun" options={{ title: "Akun" }} />
    </Stack>
  );
}
