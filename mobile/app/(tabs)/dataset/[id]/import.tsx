import * as DocumentPicker from "expo-document-picker";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { extractErrorMessage } from "@/lib/api/client";
import { useExecuteImport, useImportJob, usePreviewImport } from "@/lib/hooks/useImports";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";

export default function ImportCsvScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { colors } = useThemeColors();
  const router = useRouter();
  const showToast = useToastStore((s) => s.show);

  const previewMutation = usePreviewImport(id);
  const executeMutation = useExecuteImport(id);
  const [importJobId, setImportJobId] = useState<string | undefined>(undefined);
  const jobQuery = useImportJob(importJobId);

  const pickFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["text/csv", "text/comma-separated-values", "application/vnd.ms-excel", "*/*"],
      copyToCacheDirectory: true,
    });
    if (result.canceled || !result.assets?.[0]) return;

    const asset = result.assets[0];
    try {
      await previewMutation.mutateAsync({
        uri: asset.uri,
        name: asset.name,
        mimeType: asset.mimeType,
      });
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const handleExecute = async () => {
    if (!previewMutation.data) return;
    try {
      const job = await executeMutation.mutateAsync(previewMutation.data.upload_token);
      setImportJobId(job.id);
      showToast("Import dimulai di latar belakang.", "info");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const preview = previewMutation.data;
  const job = jobQuery.data;

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Import Ulasan dari CSV</Text>
        <Text style={[styles.description, { color: colors.textMuted }]}>
          Kolom yang didukung: reviewId/review_id, userName/username, userImage/user_image, content
          (wajib), score, thumbsUpCount/thumbs_up_count, at/review_date, appVersion/app_version.
        </Text>
        <View style={styles.actionSpacing}>
          <PrimaryButton
            label="Pilih Berkas CSV"
            onPress={pickFile}
            loading={previewMutation.isPending}
          />
        </View>
      </Card>

      {preview ? (
        <Card>
          <Text style={[styles.title, { color: colors.text }]}>Preview</Text>
          <View style={styles.badgeRow}>
            <Badge text={`Total: ${preview.total_rows}`} />
            <Badge text={`Valid: ${preview.valid_rows}`} color={colors.text} />
            <Badge text={`Tidak Valid: ${preview.invalid_rows}`} color="#DC2626" />
          </View>

          {preview.missing_required_columns.length > 0 ? (
            <Text style={styles.errorText}>
              Kolom wajib tidak ditemukan: {preview.missing_required_columns.join(", ")}
            </Text>
          ) : (
            <>
              {preview.sample_rows.slice(0, 5).map((row) => (
                <View key={row.row_number} style={styles.sampleRow}>
                  <Text style={[styles.sampleText, { color: colors.text }]} numberOfLines={2}>
                    Baris {row.row_number}: {row.data.content ?? "-"}
                  </Text>
                  <Badge text={row.is_valid ? "valid" : "tidak valid"} color={row.is_valid ? undefined : "#DC2626"} />
                </View>
              ))}
              <View style={styles.actionSpacing}>
                <PrimaryButton
                  label="Mulai Import"
                  onPress={handleExecute}
                  loading={executeMutation.isPending}
                />
              </View>
            </>
          )}
        </Card>
      ) : null}

      {job ? (
        <Card>
          <Text style={[styles.title, { color: colors.text }]}>Status Import</Text>
          <Badge text={job.status} />
          <Text style={[styles.description, { color: colors.textMuted }]}>
            Baris baru: {job.new_count} · Duplikat: {job.duplicate_count} · Tidak valid: {job.invalid_rows}
          </Text>
          {job.status === "completed" ? (
            <View style={styles.actionSpacing}>
              <PrimaryButton
                label="Lihat Ulasan"
                onPress={() => router.replace(`/(tabs)/dataset/${id}/reviews`)}
                variant="secondary"
              />
            </View>
          ) : null}
        </Card>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.xs },
  description: { fontSize: 13, marginBottom: spacing.sm },
  actionSpacing: { marginTop: spacing.sm },
  badgeRow: { flexDirection: "row", gap: spacing.xs, marginBottom: spacing.sm, flexWrap: "wrap" },
  errorText: { color: "#DC2626", fontSize: 13 },
  sampleRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.xs, gap: spacing.sm },
  sampleText: { fontSize: 12, flex: 1 },
});
