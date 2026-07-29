import { Stack } from "expo-router";

export default function ProsesLayout() {
  return (
    <Stack screenOptions={{ headerTitleAlign: "center" }}>
      <Stack.Screen name="index" options={{ title: "Proses" }} />
      <Stack.Screen name="[datasetId]/collection" options={{ title: "Kumpulkan Ulasan" }} />
      <Stack.Screen name="[datasetId]/preprocess" options={{ title: "Preprocessing" }} />
      <Stack.Screen name="[datasetId]/label" options={{ title: "Labelisasi" }} />
      <Stack.Screen name="[datasetId]/split" options={{ title: "Split Data" }} />
      <Stack.Screen name="[datasetId]/train" options={{ title: "Latih Model" }} />
      <Stack.Screen name="[datasetId]/experiment" options={{ title: "Eksperimen K" }} />
    </Stack>
  );
}
