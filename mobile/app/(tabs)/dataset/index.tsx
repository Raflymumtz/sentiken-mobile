import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useDatasets } from "@/lib/hooks/useDatasets";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { formatDate, statusLabel } from "@/lib/utils/format";
import { spacing } from "@/lib/theme";
import type { Dataset } from "@/lib/types";

export default function DatasetListScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const datasetsQuery = useDatasets();

  const onRefresh = async () => {
    setRefreshing(true);
    await datasetsQuery.refetch();
    setRefreshing(false);
  };

  if (datasetsQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat dataset..." />
      </ScreenContainer>
    );
  }

  if (datasetsQuery.isError && !datasetsQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => datasetsQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const datasets = datasetsQuery.data?.items ?? [];

  return (
    <ScreenContainer refreshing={refreshing} onRefresh={onRefresh}>
      <View style={styles.headerRow}>
        <Text style={[styles.title, { color: colors.text }]}>Dataset ({datasets.length})</Text>
        <PrimaryButton label="+ Dataset Baru" onPress={() => router.push("/(tabs)/dataset/create")} />
      </View>

      {datasets.length === 0 ? (
        <EmptyState
          title="Belum ada dataset"
          description="Buat dataset baru untuk mulai mengumpulkan atau mengimpor ulasan."
          actionLabel="Buat Dataset"
          onAction={() => router.push("/(tabs)/dataset/create")}
        />
      ) : (
        datasets.map((dataset) => <DatasetCard key={dataset.id} dataset={dataset} />)
      )}
    </ScreenContainer>
  );
}

function DatasetCard({ dataset }: { dataset: Dataset }) {
  const { colors } = useThemeColors();
  const router = useRouter();

  return (
    <Pressable
      onPress={() => router.push(`/(tabs)/dataset/${dataset.id}`)}
      accessibilityRole="button"
      accessibilityLabel={`Buka dataset ${dataset.name}`}
    >
      <Card>
        <Text style={[styles.datasetName, { color: colors.text }]}>{dataset.name}</Text>
        <Text style={[styles.datasetMeta, { color: colors.textMuted }]}>
          Aplikasi: {dataset.app_source?.app_name ?? "-"}
        </Text>
        {dataset.description ? (
          <Text style={[styles.datasetMeta, { color: colors.textMuted }]}>{dataset.description}</Text>
        ) : null}
        <Text style={[styles.datasetMeta, { color: colors.textMuted }]}>
          Periode: {dataset.period_start ? formatDate(dataset.period_start) : "-"} s.d.{" "}
          {dataset.period_end ? formatDate(dataset.period_end) : "-"}
        </Text>
        <Text style={[styles.datasetMeta, { color: colors.textMuted }]}>
          {dataset.review_count} ulasan · dibuat {formatDate(dataset.created_at)}
        </Text>
        <View style={styles.badgeRow}>
          <Badge text={`Preproc: ${statusLabel(dataset.preprocessing_status)}`} />
          <Badge text={`Label: ${statusLabel(dataset.labeling_status)}`} />
          <Badge text={`Training: ${statusLabel(dataset.training_status)}`} />
        </View>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.md,
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  title: { fontSize: 18, fontWeight: "700" },
  datasetName: { fontSize: 16, fontWeight: "700" },
  datasetMeta: { fontSize: 13, marginTop: 2 },
  badgeRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginTop: spacing.sm },
});
