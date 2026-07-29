import { Dimensions, StyleSheet, Text, View } from "react-native";
import { PieChart } from "react-native-chart-kit";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import {
  useFrequentTerms,
  useRatingDistribution,
  useSentimentComparison,
} from "@/lib/hooks/useDashboard";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";
import type { SentimentComparisonItem } from "@/lib/types";

const screenWidth = Dimensions.get("window").width - spacing.md * 2 - spacing.md * 2;

export default function PerbandinganScreen() {
  const { colors } = useThemeColors();
  const comparisonQuery = useSentimentComparison();
  const ratingQuery = useRatingDistribution();
  const termsQuery = useFrequentTerms();

  if (comparisonQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat perbandingan..." />
      </ScreenContainer>
    );
  }

  if (comparisonQuery.isError) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => comparisonQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const items = comparisonQuery.data ?? [];

  if (items.length === 0) {
    return (
      <ScreenContainer>
        <EmptyState title="Belum ada data untuk dibandingkan" />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      {items.map((item) => (
        <AppComparisonCard key={item.app_source_id} item={item} />
      ))}

      {ratingQuery.data?.map((rating) => (
        <Card key={rating.app_source_id}>
          <Text style={[styles.title, { color: colors.text }]}>
            Distribusi Rating — {rating.app_name}
          </Text>
          <View style={styles.ratingRow}>
            {Object.entries(rating.distribution).map(([star, count]) => (
              <View key={star} style={styles.ratingBar}>
                <Text style={[styles.ratingLabel, { color: colors.textMuted }]}>{star}★</Text>
                <Text style={[styles.ratingValue, { color: colors.text }]}>{count}</Text>
              </View>
            ))}
          </View>
        </Card>
      ))}

      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Term Frekuensi Tertinggi</Text>
        <Text style={[styles.description, { color: colors.textMuted }]}>
          Kata/frasa yang benar-benar ditemukan pada data ulasan (bukan kesimpulan penyebab keluhan).
        </Text>
        <View style={styles.badgeRow}>
          {(termsQuery.data ?? []).slice(0, 20).map((term) => (
            <Badge key={term.term} text={`${term.term} (${term.frequency})`} />
          ))}
        </View>
      </Card>
    </ScreenContainer>
  );
}

function AppComparisonCard({ item }: { item: SentimentComparisonItem }) {
  const { colors } = useThemeColors();
  const pieData = [
    { name: "Positif", population: item.positive_count, color: palette.positive, legendFontColor: colors.textMuted, legendFontSize: 12 },
    { name: "Negatif", population: item.negative_count, color: palette.negative, legendFontColor: colors.textMuted, legendFontSize: 12 },
    { name: "Netral", population: item.neutral_count, color: palette.neutral, legendFontColor: colors.textMuted, legendFontSize: 12 },
  ].filter((d) => d.population > 0);

  return (
    <Card>
      <Text style={[styles.title, { color: colors.text }]}>{item.app_name}</Text>
      <Text style={[styles.description, { color: colors.textMuted }]}>
        {item.total_reviews} ulasan · rating rata-rata {item.average_rating?.toFixed(2) ?? "-"}
      </Text>
      <View style={styles.badgeRow}>
        <Badge text={`Positif ${item.positive_percentage}%`} color={palette.positive} />
        <Badge text={`Negatif ${item.negative_percentage}%`} color={palette.negative} />
        <Badge text={`Netral ${item.neutral_percentage}%`} color={palette.neutral} />
      </View>
      {pieData.length > 0 ? (
        <PieChart
          data={pieData}
          width={screenWidth}
          height={160}
          chartConfig={{ color: () => colors.text }}
          accessor="population"
          backgroundColor="transparent"
          paddingLeft="8"
          style={styles.chart}
        />
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.xs },
  description: { fontSize: 12, marginBottom: spacing.sm },
  badgeRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginBottom: spacing.sm },
  chart: { marginTop: spacing.xs },
  ratingRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  ratingBar: { alignItems: "center" },
  ratingLabel: { fontSize: 11 },
  ratingValue: { fontSize: 14, fontWeight: "700" },
});
