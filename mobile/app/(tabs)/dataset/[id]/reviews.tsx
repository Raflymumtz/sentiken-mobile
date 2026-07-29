import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { useDatasetReviews } from "@/lib/hooks/useDatasets";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";
import { formatDate } from "@/lib/utils/format";

const LABEL_OPTIONS = [
  { value: undefined, label: "Semua" },
  { value: "positive", label: "Positif" },
  { value: "negative", label: "Negatif" },
  { value: "neutral", label: "Netral" },
];

export default function DatasetReviewsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { colors } = useThemeColors();
  const router = useRouter();

  const [search, setSearch] = useState("");
  const [label, setLabel] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);

  const filters = { search: search || undefined, label };
  const reviewsQuery = useDatasetReviews(id, filters, page);

  if (reviewsQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat ulasan..." />
      </ScreenContainer>
    );
  }

  if (reviewsQuery.isError) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => reviewsQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const reviews = reviewsQuery.data?.items ?? [];
  const pagination = reviewsQuery.data?.pagination;

  return (
    <ScreenContainer>
      <TextField
        label="Cari kata dalam ulasan"
        value={search}
        onChangeText={(v) => {
          setSearch(v);
          setPage(1);
        }}
        placeholder="mis. lambat, error, bagus"
      />

      <View style={styles.filterRow}>
        {LABEL_OPTIONS.map((opt) => (
          <Pressable
            key={opt.label}
            onPress={() => {
              setLabel(opt.value);
              setPage(1);
            }}
            style={[
              styles.filterChip,
              { borderColor: colors.border },
              label === opt.value && styles.filterChipActive,
            ]}
            accessibilityRole="button"
            accessibilityLabel={`Filter label ${opt.label}`}
          >
            <Text style={{ color: label === opt.value ? "#FFFFFF" : colors.text, fontSize: 12 }}>
              {opt.label}
            </Text>
          </Pressable>
        ))}
      </View>

      {reviews.length === 0 ? (
        <EmptyState title="Tidak ada ulasan" description="Coba ubah filter atau kata pencarian." />
      ) : (
        reviews.map((review) => (
          <Pressable
            key={review.id}
            onPress={() => router.push(`/(tabs)/dataset/${id}/review/${review.id}`)}
            accessibilityRole="button"
            accessibilityLabel={`Buka detail ulasan dari ${review.username ?? "pengguna"}`}
          >
            <Card>
              <View style={styles.reviewHeader}>
                <Text style={[styles.username, { color: colors.text }]}>
                  {review.username ?? "Pengguna"}
                </Text>
                <Text style={[styles.score, { color: colors.textMuted }]}>
                  {review.score ? `${review.score} / 5` : "-"}
                </Text>
              </View>
              <Text style={[styles.content, { color: colors.text }]} numberOfLines={3}>
                {review.content}
              </Text>
              <View style={styles.footerRow}>
                <Text style={[styles.date, { color: colors.textMuted }]}>
                  {formatDate(review.review_date)}
                </Text>
                {review.sentiment_labels && review.sentiment_labels.length > 0 ? (
                  <Badge text={review.sentiment_labels[0].label} />
                ) : (
                  <Badge text="Belum dilabel" color={colors.textMuted} />
                )}
              </View>
            </Card>
          </Pressable>
        ))
      )}

      {pagination && pagination.total_pages > page ? (
        <PrimaryButton label="Muat Lebih Banyak" onPress={() => setPage((p) => p + 1)} variant="secondary" />
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  filterRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginBottom: spacing.md },
  filterChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 },
  filterChipActive: { backgroundColor: "#1D4ED8", borderColor: "#1D4ED8" },
  reviewHeader: { flexDirection: "row", justifyContent: "space-between" },
  username: { fontSize: 14, fontWeight: "600" },
  score: { fontSize: 13 },
  content: { fontSize: 14, marginTop: spacing.xs },
  footerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: spacing.sm },
  date: { fontSize: 12 },
});
