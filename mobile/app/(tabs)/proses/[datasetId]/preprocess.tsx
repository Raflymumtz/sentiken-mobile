import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { extractErrorMessage } from "@/lib/api/client";
import { usePreprocessingStatus, useStartPreprocessing } from "@/lib/hooks/usePreprocessing";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import { statusLabel } from "@/lib/utils/format";

export default function PreprocessScreen() {
  const { datasetId } = useLocalSearchParams<{ datasetId: string }>();
  const { colors } = useThemeColors();
  const showToast = useToastStore((s) => s.show);
  const statusQuery = usePreprocessingStatus(datasetId);
  const startMutation = useStartPreprocessing(datasetId);

  const handleStart = async () => {
    try {
      await startMutation.mutateAsync();
      showToast("Proses preprocessing dimulai di latar belakang.", "info");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const status = statusQuery.data;

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Proses Preprocessing</Text>
        <Text style={[styles.description, { color: colors.textMuted }]}>
          Tahapan: case folding, cleaning, normalisasi kata tidak baku, tokenizing, stopword removal
          (kata negasi dipertahankan), dan stemming (Sastrawi).
        </Text>

        {status ? (
          <>
            <Badge text={statusLabel(status.status)} />
            <ProgressBar percent={status.progress_percent} />
            <Text style={[styles.description, { color: colors.textMuted }]}>
              {status.processed_reviews} / {status.total_reviews} ulasan diproses (
              {status.remaining_reviews} tersisa)
            </Text>
          </>
        ) : null}

        <PrimaryButton
          label="Jalankan Preprocessing"
          onPress={handleStart}
          loading={startMutation.isPending}
        />
      </Card>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  description: { fontSize: 13, marginBottom: spacing.sm },
});
