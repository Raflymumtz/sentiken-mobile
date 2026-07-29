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
import { useExperimentK, useTrainingRun } from "@/lib/hooks/useTraining";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import { statusLabel } from "@/lib/utils/format";

const DEFAULT_K_VALUES = "1,3,5,7,9,11";

export default function ExperimentKScreen() {
  const { datasetId, splitId } = useLocalSearchParams<{ datasetId: string; splitId?: string }>();
  const { colors } = useThemeColors();
  const router = useRouter();
  const showToast = useToastStore((s) => s.show);

  const splitsQuery = useSplits(datasetId);
  const [selectedSplitId, setSelectedSplitId] = useState<string | undefined>(splitId);
  const [kValuesText, setKValuesText] = useState(DEFAULT_K_VALUES);
  const [runId, setRunId] = useState<string | undefined>(undefined);

  const experimentMutation = useExperimentK(datasetId);
  const runQuery = useTrainingRun(runId);

  const splits = splitsQuery.data ?? [];

  const handleRun = async () => {
    if (!selectedSplitId) {
      showToast("Pilih data split terlebih dahulu.", "error");
      return;
    }
    const kValues = kValuesText
      .split(",")
      .map((v) => Number(v.trim()))
      .filter((v) => Number.isInteger(v) && v > 0);
    if (kValues.length === 0) {
      showToast("Masukkan minimal satu nilai K yang valid.", "error");
      return;
    }
    try {
      const run = await experimentMutation.mutateAsync({ data_split_id: selectedSplitId, k_values: kValues });
      setRunId(run.id);
      showToast("Eksperimen K dimulai di latar belakang.", "info");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const run = runQuery.data;

  if (splits.length === 0) {
    return (
      <ScreenContainer>
        <EmptyState title="Belum ada data split" description="Buat split data terlebih dahulu." />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Eksperimen Beberapa Nilai K</Text>

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
        <TextField
          label="Nilai K (pisahkan dengan koma)"
          value={kValuesText}
          onChangeText={setKValuesText}
          placeholder="1,3,5,7,9,11"
        />

        <PrimaryButton label="Jalankan Eksperimen" onPress={handleRun} loading={experimentMutation.isPending} />
      </Card>

      {run ? (
        <Card>
          <Text style={[styles.title, { color: colors.text }]}>Hasil Eksperimen</Text>
          <Badge text={statusLabel(run.status)} />
          {run.error_message ? <Text style={styles.errorText}>{run.error_message}</Text> : null}

          {run.items.length > 0 ? (
            <View style={styles.table}>
              <View style={styles.tableHeaderRow}>
                <Text style={[styles.th, { color: colors.textMuted }]}>K</Text>
                <Text style={[styles.th, { color: colors.textMuted }]}>Acc</Text>
                <Text style={[styles.th, { color: colors.textMuted }]}>F1</Text>
                <Text style={[styles.th, { color: colors.textMuted }]}>Waktu Latih</Text>
              </View>
              {run.items.map((item) => (
                <View
                  key={item.id}
                  style={[styles.tableRow, item.is_selected && { backgroundColor: `${colors.text}11` }]}
                >
                  <Text style={[styles.td, { color: colors.text }]}>
                    {item.k_value}
                    {item.is_selected ? " ★" : ""}
                  </Text>
                  <Text style={[styles.td, { color: colors.text }]}>{(item.accuracy * 100).toFixed(1)}%</Text>
                  <Text style={[styles.td, { color: colors.text }]}>{(item.f1_weighted * 100).toFixed(1)}%</Text>
                  <Text style={[styles.td, { color: colors.text }]}>{item.training_time_seconds.toFixed(3)}s</Text>
                </View>
              ))}
            </View>
          ) : null}

          {run.status === "completed" ? (
            <PrimaryButton
              label="Latih & Aktifkan K Terbaik"
              onPress={() =>
                router.push(`/(tabs)/proses/${datasetId}/train?splitId=${selectedSplitId ?? ""}`)
              }
              variant="secondary"
            />
          ) : null}
        </Card>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  label: { fontSize: 13, fontWeight: "600", marginBottom: spacing.xs },
  errorText: { color: "#DC2626", fontSize: 12, marginTop: spacing.xs },
  table: { marginTop: spacing.sm },
  tableHeaderRow: { flexDirection: "row", marginBottom: spacing.xs },
  tableRow: { flexDirection: "row", paddingVertical: spacing.xs },
  th: { flex: 1, fontSize: 11, fontWeight: "700" },
  td: { flex: 1, fontSize: 12 },
});
