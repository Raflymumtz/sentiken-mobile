import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useDatasets } from "@/lib/hooks/useDatasets";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";

const STEPS = [
  { key: "collection", label: "1. Kumpulkan Ulasan / Import CSV", icon: "cloud-download" },
  { key: "preprocess", label: "2. Preprocessing", icon: "construct" },
  { key: "label", label: "3. Labelisasi Kamus Sentimen", icon: "pricetags" },
  { key: "split", label: "4. Split Data Training/Testing", icon: "git-branch" },
  { key: "train", label: "5. Latih Model (TF-IDF + K-NN)", icon: "school" },
  { key: "experiment", label: "6. Eksperimen Nilai K", icon: "flask" },
] as const;

export default function ProsesIndexScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();
  const datasetsQuery = useDatasets();

  if (datasetsQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat dataset..." />
      </ScreenContainer>
    );
  }

  if (datasetsQuery.isError) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => datasetsQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const datasets = datasetsQuery.data?.items ?? [];

  if (datasets.length === 0) {
    return (
      <ScreenContainer>
        <EmptyState
          title="Belum ada dataset"
          description="Buat dataset terlebih dahulu di menu Dataset sebelum menjalankan proses."
          actionLabel="Buat Dataset"
          onAction={() => router.push("/(tabs)/dataset/create")}
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <Text style={[styles.hint, { color: colors.textMuted }]}>
        Pilih dataset, lalu jalankan tahapan proses secara berurutan.
      </Text>
      {datasets.map((dataset) => (
        <Card key={dataset.id}>
          <Text style={[styles.datasetName, { color: colors.text }]}>{dataset.name}</Text>
          <Text style={[styles.datasetMeta, { color: colors.textMuted }]}>
            {dataset.app_source?.app_name ?? "-"} · {dataset.review_count} ulasan
          </Text>
          <View style={styles.stepGrid}>
            {STEPS.map((step) => (
              <Pressable
                key={step.key}
                onPress={() => router.push(`/(tabs)/proses/${dataset.id}/${step.key}`)}
                style={[styles.stepChip, { borderColor: colors.border }]}
                accessibilityRole="button"
                accessibilityLabel={`${step.label} untuk dataset ${dataset.name}`}
              >
                <Text style={[styles.stepLabel, { color: colors.text }]}>{step.label}</Text>
              </Pressable>
            ))}
          </View>
        </Card>
      ))}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  hint: { fontSize: 13, marginBottom: spacing.md },
  datasetName: { fontSize: 15, fontWeight: "700" },
  datasetMeta: { fontSize: 12, marginTop: 2, marginBottom: spacing.sm },
  stepGrid: { gap: spacing.xs },
  stepChip: { borderWidth: 1, borderRadius: 8, padding: spacing.sm },
  stepLabel: { fontSize: 13 },
});
