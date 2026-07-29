import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import { useSplits } from "@/lib/hooks/useSplit";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useActivateTrainingRun, useTrainModel, useTrainingRun } from "@/lib/hooks/useTraining";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import { statusLabel } from "@/lib/utils/format";

export default function TrainScreen() {
  const { datasetId, splitId } = useLocalSearchParams<{ datasetId: string; splitId?: string }>();
  const { colors } = useThemeColors();
  const router = useRouter();
  const showToast = useToastStore((s) => s.show);

  const splitsQuery = useSplits(datasetId);
  const [selectedSplitId, setSelectedSplitId] = useState<string | undefined>(splitId);
  const [nNeighbors, setNNeighbors] = useState("3");
  const [activeRunId, setActiveRunId] = useState<string | undefined>(undefined);

  const trainMutation = useTrainModel(datasetId);
  const activateMutation = useActivateTrainingRun();
  const runQuery = useTrainingRun(activeRunId);

  const splits = splitsQuery.data ?? [];

  const handleTrain = async () => {
    if (!selectedSplitId) {
      showToast("Pilih data split terlebih dahulu.", "error");
      return;
    }
    try {
      const run = await trainMutation.mutateAsync({
        data_split_id: selectedSplitId,
        knn_config: { n_neighbors: Number(nNeighbors) },
      });
      setActiveRunId(run.id);
      showToast("Training dimulai di latar belakang.", "info");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const handleActivate = async () => {
    if (!activeRunId) return;
    try {
      await activateMutation.mutateAsync(activeRunId);
      showToast("Model berhasil diaktifkan.", "success");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const run = runQuery.data;

  if (splits.length === 0) {
    return (
      <ScreenContainer>
        <EmptyState
          title="Belum ada data split"
          description="Buat split data terlebih dahulu sebelum melatih model."
          actionLabel="Buat Split"
          onAction={() => router.push(`/(tabs)/proses/${datasetId}/split`)}
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Latih Model (TF-IDF + K-NN)</Text>

        <Text style={[styles.label, { color: colors.text }]}>Data Split</Text>
        {splits.map((split) => (
          <PrimaryButton
            key={split.id}
            label={`Train ${split.train_count} / Test ${split.test_count} (${split.label_mode})`}
            onPress={() => setSelectedSplitId(split.id)}
            variant={selectedSplitId === split.id ? "primary" : "secondary"}
          />
        ))}

        <View style={{ height: spacing.sm }} />
        <TextField label="Nilai K (n_neighbors)" value={nNeighbors} onChangeText={setNNeighbors} keyboardType="numeric" />

        <PrimaryButton label="Latih Model" onPress={handleTrain} loading={trainMutation.isPending} />
      </Card>

      {run ? (
        <Card>
          <Text style={[styles.title, { color: colors.text }]}>Status Training</Text>
          <Badge text={statusLabel(run.status)} />
          {run.error_message ? <Text style={styles.errorText}>{run.error_message}</Text> : null}
          {run.status === "completed" ? (
            <View style={styles.actionColumn}>
              <Text style={[styles.meta, { color: colors.textMuted }]}>
                Model version: {run.model_version} · aktif: {run.is_active ? "ya" : "tidak"}
              </Text>
              <PrimaryButton
                label="Lihat Hasil Evaluasi"
                onPress={() => router.push(`/(tabs)/analisis/evaluasi/${run.id}`)}
                variant="secondary"
              />
              {!run.is_active ? (
                <PrimaryButton
                  label="Aktifkan Model Ini"
                  onPress={handleActivate}
                  loading={activateMutation.isPending}
                />
              ) : null}
            </View>
          ) : null}
        </Card>
      ) : null}

      <PrimaryButton
        label="Coba Eksperimen Beberapa Nilai K"
        onPress={() =>
          router.push(
            `/(tabs)/proses/${datasetId}/experiment${selectedSplitId ? `?splitId=${selectedSplitId}` : ""}`,
          )
        }
        variant="secondary"
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  label: { fontSize: 13, fontWeight: "600", marginBottom: spacing.xs },
  meta: { fontSize: 12, marginBottom: spacing.xs },
  errorText: { color: "#DC2626", fontSize: 12, marginTop: spacing.xs },
  actionColumn: { gap: spacing.sm, marginTop: spacing.sm },
});
