import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { StatCard } from "@/components/ui/StatCard";
import { extractErrorMessage } from "@/lib/api/client";
import { useDataset, useDatasetSummary, useDeleteDataset } from "@/lib/hooks/useDatasets";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import { statusLabel } from "@/lib/utils/format";

export default function DatasetDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { colors } = useThemeColors();
  const router = useRouter();
  const showToast = useToastStore((s) => s.show);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const datasetQuery = useDataset(id);
  const summaryQuery = useDatasetSummary(id);
  const deleteDataset = useDeleteDataset();

  if (datasetQuery.isLoading || summaryQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat detail dataset..." />
      </ScreenContainer>
    );
  }

  if (datasetQuery.isError || !datasetQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => datasetQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const dataset = datasetQuery.data;
  const summary = summaryQuery.data;

  const handleDelete = async () => {
    try {
      await deleteDataset.mutateAsync(dataset.id);
      showToast("Dataset dihapus.", "success");
      router.replace("/(tabs)/dataset");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    } finally {
      setConfirmDelete(false);
    }
  };

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>{dataset.name}</Text>
        <Text style={[styles.meta, { color: colors.textMuted }]}>
          Aplikasi: {dataset.app_source?.app_name ?? "-"}
        </Text>
        {dataset.description ? (
          <Text style={[styles.meta, { color: colors.textMuted }]}>{dataset.description}</Text>
        ) : null}
        <View style={styles.badgeRow}>
          <Badge text={`Preproc: ${statusLabel(dataset.preprocessing_status)}`} />
          <Badge text={`Label: ${statusLabel(dataset.labeling_status)}`} />
          <Badge text={`Training: ${statusLabel(dataset.training_status)}`} />
          <Badge text={dataset.label_mode === "binary" ? "Binary" : "Ternary"} />
        </View>
      </Card>

      {summary ? (
        <View style={styles.statsGrid}>
          <StatCard label="Total Ulasan" value={summary.total_reviews} />
          <StatCard label="Positif" value={summary.label_distribution.positive ?? 0} />
          <StatCard label="Negatif" value={summary.label_distribution.negative ?? 0} />
          <StatCard label="Netral" value={summary.label_distribution.neutral ?? 0} />
        </View>
      ) : null}

      <Card>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Aksi</Text>
        <View style={styles.actionsColumn}>
          <PrimaryButton
            label="Lihat Ulasan"
            onPress={() => router.push(`/(tabs)/dataset/${dataset.id}/reviews`)}
            variant="secondary"
          />
          <PrimaryButton
            label="Import CSV"
            onPress={() => router.push(`/(tabs)/dataset/${dataset.id}/import`)}
            variant="secondary"
          />
          <PrimaryButton
            label="Kumpulkan Ulasan (Proses)"
            onPress={() => router.push(`/(tabs)/proses/${dataset.id}/collection`)}
            variant="secondary"
          />
          <PrimaryButton
            label="Jalankan Pipeline (Proses)"
            onPress={() => router.push(`/(tabs)/proses/${dataset.id}/preprocess`)}
          />
          <PrimaryButton
            label="Hapus Dataset"
            onPress={() => setConfirmDelete(true)}
            variant="danger"
          />
        </View>
      </Card>

      <ConfirmDialog
        visible={confirmDelete}
        title="Hapus Dataset?"
        description={`Dataset "${dataset.name}" akan dihapus (soft delete). Data ulasan tetap tersimpan di database.`}
        confirmLabel="Hapus"
        destructive
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 18, fontWeight: "700" },
  meta: { fontSize: 13, marginTop: 4 },
  badgeRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginTop: spacing.sm },
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginBottom: spacing.sm },
  sectionTitle: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  actionsColumn: { gap: spacing.sm },
});
