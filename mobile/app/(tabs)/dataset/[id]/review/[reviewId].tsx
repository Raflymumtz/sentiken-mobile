import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { useReviewDetail } from "@/lib/hooks/useReviews";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";
import { formatDateTime } from "@/lib/utils/format";

export default function ReviewDetailScreen() {
  const { reviewId } = useLocalSearchParams<{ reviewId: string }>();
  const { colors } = useThemeColors();
  const query = useReviewDetail(reviewId);

  if (query.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat detail ulasan..." />
      </ScreenContainer>
    );
  }

  if (query.isError && !query.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => query.refetch()} />
      </ScreenContainer>
    );
  }

  const review = query.data;
  if (!review) return null;
  const label = review.sentiment_labels?.[0];
  const pre = review.preprocessing_result;

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Ulasan Asli</Text>
        <Text style={[styles.body, { color: colors.text }]}>{review.content}</Text>
        <View style={styles.metaGrid}>
          <MetaItem label="Pengguna" value={review.username ?? "-"} colors={colors} />
          <MetaItem label="Rating" value={review.score ? `${review.score} / 5` : "-"} colors={colors} />
          <MetaItem label="Tanggal" value={formatDateTime(review.review_date)} colors={colors} />
          <MetaItem label="Thumbs Up" value={String(review.thumbs_up_count)} colors={colors} />
          <MetaItem label="Versi Aplikasi" value={review.app_version ?? "-"} colors={colors} />
          <MetaItem label="Sumber" value={review.source} colors={colors} />
        </View>
      </Card>

      <Card>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Hasil Preprocessing</Text>
        {pre ? (
          <View style={styles.stageList}>
            <StageItem label="1. Case Folding" value={pre.case_folded_text} colors={colors} />
            <StageItem label="2. Cleaning" value={pre.cleaned_text} colors={colors} />
            <StageItem label="3. Normalisasi" value={pre.normalized_text} colors={colors} />
            <StageItem label="4. Tokenizing" value={pre.tokens.join(", ")} colors={colors} />
            <StageItem label="5. Stopword Removal" value={pre.tokens_no_stopword.join(", ")} colors={colors} />
            <StageItem label="6. Stemming" value={pre.stemmed_text} colors={colors} />
            <StageItem label="7. Final Text" value={pre.final_text} colors={colors} />
          </View>
        ) : (
          <Text style={{ color: colors.textMuted }}>Belum diproses. Jalankan preprocessing pada menu Proses.</Text>
        )}
      </Card>

      <Card>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Labelisasi & Prediksi</Text>
        {label ? (
          <View style={styles.metaGrid}>
            <MetaItem label="Skor Positif" value={label.positive_score.toFixed(2)} colors={colors} />
            <MetaItem label="Skor Negatif" value={label.negative_score.toFixed(2)} colors={colors} />
            <MetaItem label="Skor Total" value={label.sentiment_score.toFixed(2)} colors={colors} />
          </View>
        ) : (
          <Text style={{ color: colors.textMuted }}>Belum dilabel.</Text>
        )}
        <View style={styles.badgeRow}>
          {label ? <Badge text={`Label aktual: ${label.label}`} /> : null}
          {review.predicted_label ? <Badge text={`Prediksi: ${review.predicted_label}`} /> : null}
        </View>

        {review.nearest_neighbors && review.nearest_neighbors.length > 0 ? (
          <View style={styles.neighborList}>
            <Text style={[styles.subheading, { color: colors.text }]}>Tetangga Terdekat</Text>
            {review.nearest_neighbors.map((n, idx) => (
              <View key={idx} style={styles.neighborRow}>
                <Text style={[styles.neighborText, { color: colors.text }]} numberOfLines={2}>
                  {idx + 1}. {n.text}
                </Text>
                <Text style={[styles.neighborMeta, { color: colors.textMuted }]}>
                  {n.label} · jarak {n.distance.toFixed(4)}
                </Text>
              </View>
            ))}
          </View>
        ) : null}
      </Card>
    </ScreenContainer>
  );
}

function MetaItem({ label, value, colors }: { label: string; value: string; colors: { text: string; textMuted: string } }) {
  return (
    <View style={styles.metaItem}>
      <Text style={[styles.metaLabel, { color: colors.textMuted }]}>{label}</Text>
      <Text style={[styles.metaValue, { color: colors.text }]}>{value}</Text>
    </View>
  );
}

function StageItem({ label, value, colors }: { label: string; value: string; colors: { text: string; textMuted: string } }) {
  return (
    <View style={styles.stageItem}>
      <Text style={[styles.stageLabel, { color: colors.textMuted }]}>{label}</Text>
      <Text style={[styles.stageValue, { color: colors.text }]}>{value || "-"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  sectionTitle: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  body: { fontSize: 14, lineHeight: 20 },
  metaGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md, marginTop: spacing.sm },
  metaItem: { minWidth: "40%" },
  metaLabel: { fontSize: 11 },
  metaValue: { fontSize: 13, fontWeight: "600" },
  stageList: { gap: spacing.sm },
  stageItem: { marginBottom: spacing.xs },
  stageLabel: { fontSize: 11, fontWeight: "700" },
  stageValue: { fontSize: 13, marginTop: 2 },
  badgeRow: { flexDirection: "row", gap: spacing.xs, marginTop: spacing.sm },
  neighborList: { marginTop: spacing.md },
  subheading: { fontSize: 13, fontWeight: "700", marginBottom: spacing.xs },
  neighborRow: { marginBottom: spacing.xs },
  neighborText: { fontSize: 12 },
  neighborMeta: { fontSize: 11 },
});
