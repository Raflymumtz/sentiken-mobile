import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useDatasets } from "@/lib/hooks/useDatasets";
import { useTrainingRuns } from "@/lib/hooks/useTraining";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";
import type { Dataset } from "@/lib/types";
import { formatDateTime, statusLabel } from "@/lib/utils/format";

export default function AnalisisIndexScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();
  const datasetsQuery = useDatasets();

  return (
    <ScreenContainer>
      <View style={styles.menuRow}>
        <Pressable
          style={[styles.menuCard, { borderColor: colors.border, backgroundColor: colors.surface }]}
          onPress={() => router.push("/(tabs)/analisis/prediksi")}
          accessibilityRole="button"
          accessibilityLabel="Buka Prediksi Satu Teks"
        >
          <Text style={[styles.menuTitle, { color: colors.text }]}>Prediksi Satu Teks</Text>
          <Text style={[styles.menuDesc, { color: colors.textMuted }]}>Uji model dengan teks ulasan baru</Text>
        </Pressable>
        <Pressable
          style={[styles.menuCard, { borderColor: colors.border, backgroundColor: colors.surface }]}
          onPress={() => router.push("/(tabs)/analisis/perbandingan")}
          accessibilityRole="button"
          accessibilityLabel="Buka Perbandingan Aplikasi"
        >
          <Text style={[styles.menuTitle, { color: colors.text }]}>Perbandingan Aplikasi</Text>
          <Text style={[styles.menuDesc, { color: colors.textMuted }]}>PLN Mobile vs MyPertamina</Text>
        </Pressable>
      </View>

      <Text style={[styles.sectionTitle, { color: colors.text }]}>Hasil Evaluasi per Dataset</Text>
      {(datasetsQuery.data?.items ?? []).length === 0 ? (
        <EmptyState title="Belum ada dataset" />
      ) : (
        (datasetsQuery.data?.items ?? []).map((dataset) => <DatasetRuns key={dataset.id} dataset={dataset} />)
      )}
    </ScreenContainer>
  );
}

function DatasetRuns({ dataset }: { dataset: Dataset }) {
  const { colors } = useThemeColors();
  const router = useRouter();
  const runsQuery = useTrainingRuns(dataset.id, "single");
  const runs = (runsQuery.data?.items ?? []).filter((r) => r.status === "completed");

  if (runs.length === 0) return null;

  return (
    <Card>
      <Text style={[styles.datasetName, { color: colors.text }]}>{dataset.name}</Text>
      {runs.map((run) => (
        <Pressable
          key={run.id}
          onPress={() => router.push(`/(tabs)/analisis/evaluasi/${run.id}`)}
          style={styles.runRow}
          accessibilityRole="button"
          accessibilityLabel={`Lihat evaluasi model ${run.model_version}`}
        >
          <View>
            <Text style={{ color: colors.text, fontSize: 13 }}>{run.model_version}</Text>
            <Text style={{ color: colors.textMuted, fontSize: 11 }}>{formatDateTime(run.created_at)}</Text>
          </View>
          {run.is_active ? <Badge text="Aktif" /> : <Badge text={statusLabel(run.status)} />}
        </Pressable>
      ))}
    </Card>
  );
}

const styles = StyleSheet.create({
  menuRow: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.lg },
  menuCard: { flex: 1, borderWidth: 1, borderRadius: 12, padding: spacing.md, minHeight: 90 },
  menuTitle: { fontSize: 14, fontWeight: "700" },
  menuDesc: { fontSize: 12, marginTop: spacing.xs },
  sectionTitle: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  datasetName: { fontSize: 14, fontWeight: "700", marginBottom: spacing.xs },
  runRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: spacing.xs,
  },
});
