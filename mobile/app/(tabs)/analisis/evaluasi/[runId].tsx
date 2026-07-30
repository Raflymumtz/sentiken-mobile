import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { StatCard } from "@/components/ui/StatCard";
import { useEvaluationMetrics } from "@/lib/hooks/useEvaluation";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { downloadAndShare } from "@/lib/utils/download";
import { spacing } from "@/lib/theme";

export default function EvaluasiDetailScreen() {
  const { runId } = useLocalSearchParams<{ runId: string }>();
  const { colors } = useThemeColors();
  const metricsQuery = useEvaluationMetrics(runId);

  if (metricsQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat hasil evaluasi..." />
      </ScreenContainer>
    );
  }

  if (metricsQuery.isError && !metricsQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState message="Hasil evaluasi belum tersedia." onRetry={() => metricsQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const metrics = metricsQuery.data;
  if (!metrics) return null;
  const { labels, matrix } = metrics.confusion_matrix;

  return (
    <ScreenContainer>
      <View style={styles.statsGrid}>
        <StatCard label="Accuracy" value={`${(metrics.accuracy * 100).toFixed(1)}%`} />
        <StatCard label="Precision (weighted)" value={`${(metrics.precision_weighted * 100).toFixed(1)}%`} />
        <StatCard label="Recall (weighted)" value={`${(metrics.recall_weighted * 100).toFixed(1)}%`} />
        <StatCard label="F1-score (weighted)" value={`${(metrics.f1_weighted * 100).toFixed(1)}%`} />
        <StatCard label="Precision (macro)" value={`${(metrics.precision_macro * 100).toFixed(1)}%`} />
        <StatCard label="Recall (macro)" value={`${(metrics.recall_macro * 100).toFixed(1)}%`} />
        <StatCard label="F1-score (macro)" value={`${(metrics.f1_macro * 100).toFixed(1)}%`} />
      </View>

      {metrics.warnings.length > 0 ? (
        <Card>
          {metrics.warnings.map((w, idx) => (
            <Text key={idx} style={styles.warning}>
              ⚠ {w}
            </Text>
          ))}
        </Card>
      ) : null}

      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Confusion Matrix</Text>
        <View style={styles.matrixTable}>
          <View style={styles.matrixRow}>
            <Text style={[styles.matrixCell, styles.matrixHeader, { color: colors.textMuted }]}> </Text>
            {labels.map((label) => (
              <Text key={label} style={[styles.matrixCell, styles.matrixHeader, { color: colors.textMuted }]}>
                {label}
              </Text>
            ))}
          </View>
          {matrix.map((row, i) => (
            <View key={i} style={styles.matrixRow}>
              <Text style={[styles.matrixCell, styles.matrixHeader, { color: colors.textMuted }]}>
                {labels[i]}
              </Text>
              {row.map((value, j) => (
                <Text
                  key={j}
                  style={[
                    styles.matrixCell,
                    { color: colors.text, fontWeight: i === j ? "700" : "400" },
                  ]}
                >
                  {value}
                </Text>
              ))}
            </View>
          ))}
        </View>
      </Card>

      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Support per Kelas</Text>
        <View style={styles.badgeRow}>
          {Object.entries(metrics.support).map(([label, count]) => (
            <Badge key={label} text={`${label}: ${count}`} />
          ))}
        </View>
      </Card>

      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Ekspor</Text>
        <View style={styles.exportColumn}>
          <PrimaryButton
            label="Unduh Confusion Matrix (PNG)"
            variant="secondary"
            onPress={() =>
              downloadAndShare(
                `/training-runs/${runId}/export/confusion-matrix.png`,
                `confusion_matrix_${runId}.png`,
              )
            }
          />
          <PrimaryButton
            label="Unduh Ringkasan (PDF)"
            variant="secondary"
            onPress={() =>
              downloadAndShare(`/training-runs/${runId}/export/summary.pdf`, `summary_${runId}.pdf`)
            }
          />
          <PrimaryButton
            label="Unduh Prediksi (CSV)"
            variant="secondary"
            onPress={() =>
              downloadAndShare(`/training-runs/${runId}/export/predictions`, `predictions_${runId}.csv`)
            }
          />
        </View>
      </Card>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginBottom: spacing.sm },
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  warning: { color: "#CA8A04", fontSize: 12, marginBottom: spacing.xs },
  matrixTable: { marginTop: spacing.xs },
  matrixRow: { flexDirection: "row" },
  matrixCell: { flex: 1, fontSize: 12, textAlign: "center", paddingVertical: spacing.xs },
  matrixHeader: { fontWeight: "700" },
  badgeRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  exportColumn: { gap: spacing.sm },
});
