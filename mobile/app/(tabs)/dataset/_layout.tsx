import { Stack } from "expo-router";

export default function DatasetLayout() {
  return (
    <Stack screenOptions={{ headerTitleAlign: "center" }}>
      <Stack.Screen name="index" options={{ title: "Dataset" }} />
      <Stack.Screen name="create" options={{ title: "Dataset Baru", presentation: "modal" }} />
      <Stack.Screen name="[id]/index" options={{ title: "Detail Dataset" }} />
      <Stack.Screen name="[id]/reviews" options={{ title: "Daftar Ulasan" }} />
      <Stack.Screen name="[id]/import" options={{ title: "Import CSV" }} />
      <Stack.Screen name="[id]/review/[reviewId]" options={{ title: "Detail Ulasan" }} />
    </Stack>
  );
}
