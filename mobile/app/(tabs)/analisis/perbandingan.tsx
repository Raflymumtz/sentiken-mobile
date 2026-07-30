import { Dimensions, StyleSheet, Text, View } from "react-native";
import { PieChart } from "react-native-chart-kit";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import {
  useAspectComparison,
  useFrequentTerms,
  useRatingDistribution,
  useSentimentComparison,
} from "@/lib/hooks/useDashboard";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";
import type { AppAspectComparisonItem, SentimentComparisonItem } from "@/lib/types";

const ASPECT_LABELS: Record<string, { title: string; winnerSuffix: string }> = {
  kecepatan: { title: "Kecepatan", winnerSuffix: "lebih cepat" },
  kemudahan: { title: "Kemudahan", winnerSuffix: "lebih mudah digunakan" },
};

const screenWidth = Dimensions.get("window").width - spacing.md * 2 - spacing.md * 2;

export default function PerbandinganScreen() {
  const { colors } = useThemeColors();
  const comparisonQuery = useSentimentComparison();
  const ratingQuery = useRatingDistribution();
  const termsQuery = useFrequentTerms();
  const aspectQuery = useAspectComparison();

  if (comparisonQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat perbandingan..." />
      </ScreenContainer>
    );
  }

  if (comparisonQuery.isError && !comparisonQuery.data) {
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
      {aspectQuery.data && aspectQuery.data.length > 0 ? (
        <AspectComparisonSection items={aspectQuery.data} />
      ) : null}

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

function AspectComparisonSection({ items }: { items: AppAspectComparisonItem[] }) {
  const { colors } = useThemeColors();
  const aspectKeys = Array.from(
    new Set(items.flatMap((item) => item.aspects.map((a) => a.aspect))),
  ).filter((key) => key in ASPECT_LABELS);

  return (
    <Card>
      <Text style={[styles.title, { color: colors.text }]}>
        Perbandingan Kecepatan &amp; Kemudahan
      </Text>
      <Text style={[styles.description, { color: colors.textMuted }]}>
        Dihitung dari ulasan yang benar-benar menyebut kata terkait kecepatan/kemudahan (mis. cepat,
        lambat, mudah, ribet), berdasarkan sentimen ulasan tersebut.
      </Text>

      {aspectKeys.map((aspectKey) => {
        const label = ASPECT_LABELS[aspectKey];
        const rows = items
          .map((item) => ({
            app_name: item.app_name,
            aspect: item.aspects.find((a) => a.aspect === aspectKey),
          }))
          .filter((row): row is { app_name: string; aspect: AppAspectComparisonItem["aspects"][number] } =>
            !!row.aspect,
          );

        const withMentions = rows.filter((row) => row.aspect.total_mentions > 0);
        const winner =
          withMentions.length >= 2
            ? withMentions.reduce((best, row) =>
                row.aspect.positive_percentage > best.aspect.positive_percentage ? row : best,
              )
            : null;

        return (
          <View key={aspectKey} style={styles.aspectBlock}>
            <Text style={[styles.aspectTitle, { color: colors.text }]}>{label.title}</Text>

            {rows.map((row) => (
              <View key={row.app_name} style={styles.aspectRow}>
                <Text style={[styles.aspectAppName, { color: colors.text }]}>{row.app_name}</Text>
                {row.aspect.total_mentions > 0 ? (
                  <View style={styles.badgeRow}>
                    <Badge
                      text={`Positif ${row.aspect.positive_percentage}%`}
                      color={palette.positive}
                    />
                    <Badge
                      text={`Negatif ${row.aspect.negative_percentage}%`}
                      color={palette.negative}
                    />
                    <Text style={[styles.aspectMentionCount, { color: colors.textMuted }]}>
                      ({row.aspect.total_mentions} ulasan menyebut ini)
                    </Text>
                  </View>
                ) : (
                  <Text style={[styles.aspectMentionCount, { color: colors.textMuted }]}>
                    Belum ada ulasan yang menyebut aspek ini.
                  </Text>
                )}
              </View>
            ))}

            {winner ? (
              <Text style={[styles.aspectWinner, { color: palette.positive }]}>
                🏆 {winner.app_name} {label.winnerSuffix} menurut ulasan pengguna.
              </Text>
            ) : (
              <Text style={[styles.aspectMentionCount, { color: colors.textMuted }]}>
                Data belum cukup untuk membandingkan aspek ini di kedua aplikasi.
              </Text>
            )}
          </View>
        );
      })}
    </Card>
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
  aspectBlock: { marginTop: spacing.sm, paddingTop: spacing.sm, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: "#8884" },
  aspectTitle: { fontSize: 14, fontWeight: "700", marginBottom: spacing.xs },
  aspectRow: { marginBottom: spacing.xs },
  aspectAppName: { fontSize: 13, fontWeight: "600", marginBottom: 2 },
  aspectMentionCount: { fontSize: 11 },
  aspectWinner: { fontSize: 13, fontWeight: "700", marginTop: spacing.xs },
  chart: { marginTop: spacing.xs },
  ratingRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  ratingBar: { alignItems: "center" },
  ratingLabel: { fontSize: 11 },
  ratingValue: { fontSize: 14, fontWeight: "700" },
});
