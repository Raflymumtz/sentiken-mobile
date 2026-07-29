import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import { useCreateSplit, useSplits } from "@/lib/hooks/useSplit";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import { formatDateTime } from "@/lib/utils/format";

export default function SplitScreen() {
  const { datasetId } = useLocalSearchParams<{ datasetId: string }>();
  const { colors } = useThemeColors();
  const router = useRouter();
  const showToast = useToastStore((s) => s.show);

  const [trainSize, setTrainSize] = useState("0.8");
  const [testSize, setTestSize] = useState("0.2");
  const [randomState, setRandomState] = useState("42");
  const [stratify, setStratify] = useState(true);
  const [labelMode, setLabelMode] = useState<"binary" | "ternary">("binary");

  const splitsQuery = useSplits(datasetId);
  const createSplit = useCreateSplit(datasetId);

  const handleCreate = async () => {
    try {
      await createSplit.mutateAsync({
        train_size: Number(trainSize),
        test_size: Number(testSize),
        random_state: Number(randomState),
        stratify,
        label_mode: labelMode,
      });
      showToast("Split data berhasil dibuat.", "success");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const splits = splitsQuery.data ?? [];

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Split Data Training/Testing</Text>

        <TextField label="Train Size" value={trainSize} onChangeText={setTrainSize} keyboardType="decimal-pad" />
        <TextField label="Test Size" value={testSize} onChangeText={setTestSize} keyboardType="decimal-pad" />
        <TextField label="Random State" value={randomState} onChangeText={setRandomState} keyboardType="numeric" />

        <Text style={[styles.label, { color: colors.text }]}>Mode Label</Text>
        <View style={styles.row}>
          {(["binary", "ternary"] as const).map((m) => (
            <PrimaryButton
              key={m}
              label={m}
              onPress={() => setLabelMode(m)}
              variant={labelMode === m ? "primary" : "secondary"}
            />
          ))}
        </View>

        <Text style={[styles.label, { color: colors.text }]}>Stratify</Text>
        <View style={styles.row}>
          <PrimaryButton label="Aktif" onPress={() => setStratify(true)} variant={stratify ? "primary" : "secondary"} />
          <PrimaryButton label="Nonaktif" onPress={() => setStratify(false)} variant={!stratify ? "primary" : "secondary"} />
        </View>

        <PrimaryButton label="Buat Split" onPress={handleCreate} loading={createSplit.isPending} />
      </Card>

      {splits.length === 0 ? (
        <EmptyState title="Belum ada split" description="Buat split data terlebih dahulu." />
      ) : (
        splits.map((split) => (
          <Card key={split.id}>
            <Text style={[styles.splitTitle, { color: colors.text }]}>
              Train {split.train_count} / Test {split.test_count} ({split.label_mode})
            </Text>
            <Text style={[styles.meta, { color: colors.textMuted }]}>
              random_state={split.random_state} · stratify={String(split.stratify)}
            </Text>
            <Text style={[styles.meta, { color: colors.textMuted }]}>{formatDateTime(split.created_at)}</Text>
            <PrimaryButton
              label="Latih Model dengan Split Ini"
              onPress={() => router.push(`/(tabs)/proses/${datasetId}/train?splitId=${split.id}`)}
              variant="secondary"
            />
          </Card>
        ))
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  label: { fontSize: 13, fontWeight: "600", marginBottom: spacing.xs },
  row: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.md },
  splitTitle: { fontSize: 14, fontWeight: "700" },
  meta: { fontSize: 12, marginTop: 2, marginBottom: spacing.sm },
});
