import { Stack } from "expo-router";

export default function AnalisisLayout() {
  return (
    <Stack screenOptions={{ headerTitleAlign: "center" }}>
      <Stack.Screen name="index" options={{ title: "Analisis" }} />
      <Stack.Screen name="evaluasi/[runId]" options={{ title: "Hasil Evaluasi" }} />
      <Stack.Screen name="prediksi" options={{ title: "Prediksi Satu Teks" }} />
      <Stack.Screen name="perbandingan" options={{ title: "Perbandingan Aplikasi" }} />
    </Stack>
  );
}
