import { useState } from "react";
import { Dimensions, StyleSheet, Text, View } from "react-native";
import { BarChart, LineChart } from "react-native-chart-kit";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { StatCard } from "@/components/ui/StatCard";
import { useDashboardSummary, useSentimentComparison, useSentimentTrend } from "@/lib/hooks/useDashboard";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";

const screenWidth = Dimensions.get("window").width - spacing.md * 2 - spacing.md * 2;

export default function DashboardScreen() {
  const { colors } = useThemeColors();
  const [refreshing, setRefreshing] = useState(false);
  const summaryQuery = useDashboardSummary();
  const comparisonQuery = useSentimentComparison();
  const trendQuery = useSentimentTrend("month");

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([summaryQuery.refetch(), comparisonQuery.refetch(), trendQuery.refetch()]);
    setRefreshing(false);
  };

  if (summaryQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat dashboard..." />
      </ScreenContainer>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => summaryQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const summary = summaryQuery.data;

  if (!summary.has_data) {
    return (
      <ScreenContainer refreshing={refreshing} onRefresh={onRefresh}>
        <EmptyState
          title="Belum ada dataset"
          description="Tambahkan sumber aplikasi dan dataset, lalu kumpulkan atau impor data ulasan untuk mulai menganalisis sentimen."
        />
      </ScreenContainer>
    );
  }

  const chartConfig = {
    backgroundGradientFrom: colors.surface,
    backgroundGradientTo: colors.surface,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(29, 78, 216, ${opacity})`,
    labelColor: () => colors.textMuted,
    barPercentage: 0.6,
  };

  const comparisonLabels = (comparisonQuery.data ?? []).map((c) => c.app_name);
  const comparisonPositive = (comparisonQuery.data ?? []).map((c) => c.positive_count);
  const comparisonNegative = (comparisonQuery.data ?? []).map((c) => c.negative_count);

  const trendPeriods = Array.from(new Set((trendQuery.data ?? []).map((p) => p.period))).sort();
  const trendPositiveByPeriod = trendPeriods.map((period) =>
    (trendQuery.data ?? [])
      .filter((p) => p.period === period)
      .reduce((sum, p) => sum + p.positive_count, 0),
  );

  return (
    <ScreenContainer refreshing={refreshing} onRefresh={onRefresh}>
      <View style={styles.statsGrid}>
        <StatCard label="Total Dataset" value={summary.total_datasets} />
        <StatCard label="Total Ulasan" value={summary.total_reviews} />
        <StatCard label="Ulasan PLN Mobile" value={summary.total_reviews_pln_mobile} />
        <StatCard label="Ulasan MyPertamina" value={summary.total_reviews_mypertamina} />
        <StatCard label="Positif" value={summary.sentiment_counts.positive} accentColor={palette.positive} />
        <StatCard label="Negatif" value={summary.sentiment_counts.negative} accentColor={palette.negative} />
        <StatCard label="Netral" value={summary.sentiment_counts.neutral} accentColor={palette.neutral} />
        <StatCard
          label="Persentase Positif"
          value={`${summary.sentiment_percentage.positive}%`}
          accentColor={palette.positive}
        />
      </View>

      <Card>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Model Aktif</Text>
        {summary.active_model_version ? (
          <View>
            <Text style={[styles.modelVersion, { color: colors.text }]}>{summary.active_model_version}</Text>
            <Text style={[styles.modelDetail, { color: colors.textMuted }]}>Nilai K: {summary.active_k}</Text>
            {summary.active_metrics ? (
              <View style={styles.metricsRow}>
                <Text style={[styles.metric, { color: colors.textMuted }]}>
                  Accuracy: {(summary.active_metrics.accuracy * 100).toFixed(1)}%
                </Text>
                <Text style={[styles.metric, { color: colors.textMuted }]}>
                  Precision: {(summary.active_metrics.precision * 100).toFixed(1)}%
                </Text>
                <Text style={[styles.metric, { color: colors.textMuted }]}>
                  Recall: {(summary.active_metrics.recall * 100).toFixed(1)}%
                </Text>
                <Text style={[styles.metric, { color: colors.textMuted }]}>
                  F1-score: {(summary.active_metrics.f1_score * 100).toFixed(1)}%
                </Text>
              </View>
            ) : null}
          </View>
        ) : (
          <Text style={[styles.modelDetail, { color: colors.textMuted }]}>
            Model belum dilatih. Jalankan pipeline preprocessing, labelisasi, split, dan training pada
            menu Proses.
          </Text>
        )}
      </Card>

      <Card>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Job Terbaru</Text>
        {summary.latest_job_status ? (
          <View style={styles.jobRow}>
            <Badge text={summary.latest_job_status} />
            <Text style={[styles.modelDetail, { color: colors.textMuted }]}>
              Tipe: {summary.latest_job_type === "collection" ? "Pengumpulan Data" : "Import CSV"}
            </Text>
          </View>
        ) : (
          <Text style={[styles.modelDetail, { color: colors.textMuted }]}>Belum ada job yang dijalankan.</Text>
        )}
      </Card>

      {comparisonLabels.length > 0 ? (
        <Card>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Perbandingan Sentimen Aplikasi</Text>
          <BarChart
            data={{
              labels: comparisonLabels,
              datasets: [{ data: comparisonPositive }, { data: comparisonNegative }],
            }}
            width={screenWidth}
            height={200}
            chartConfig={chartConfig}
            yAxisLabel=""
            yAxisSuffix=""
            fromZero
            style={styles.chart}
          />
          <View style={styles.legendRow}>
            <Text style={{ color: palette.positive }}>■ Positif</Text>
            <Text style={{ color: palette.negative }}>■ Negatif</Text>
          </View>
        </Card>
      ) : null}

      {trendPeriods.length > 1 ? (
        <Card>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Tren Sentimen Positif</Text>
          <LineChart
            data={{ labels: trendPeriods, datasets: [{ data: trendPositiveByPeriod }] }}
            width={screenWidth}
            height={200}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </Card>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginBottom: spacing.sm },
  sectionTitle: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  modelVersion: { fontSize: 14, fontWeight: "600" },
  modelDetail: { fontSize: 13, marginTop: 2 },
  metricsRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md, marginTop: spacing.sm },
  metric: { fontSize: 12 },
  jobRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  chart: { borderRadius: 8, marginTop: spacing.sm },
  legendRow: { flexDirection: "row", gap: spacing.md, marginTop: spacing.xs, justifyContent: "center" },
});
