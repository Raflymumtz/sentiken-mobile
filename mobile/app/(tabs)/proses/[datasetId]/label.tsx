import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { StatCard } from "@/components/ui/StatCard";
import { extractErrorMessage } from "@/lib/api/client";
import { useLabelSummary, useStartLabeling } from "@/lib/hooks/useLabeling";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { palette, spacing } from "@/lib/theme";
import { statusLabel } from "@/lib/utils/format";

export default function LabelScreen() {
  const { datasetId } = useLocalSearchParams<{ datasetId: string }>();
  const { colors } = useThemeColors();
  const showToast = useToastStore((s) => s.show);
  const [mode, setMode] = useState<"binary" | "ternary">("binary");

  const summaryQuery = useLabelSummary(datasetId);
  const startMutation = useStartLabeling(datasetId);

  const handleStart = async () => {
    try {
      await startMutation.mutateAsync(mode);
      showToast(`Labelisasi mode ${mode} dimulai.`, "info");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const summary = summaryQuery.data;

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Labelisasi Kamus Sentimen</Text>
        <Text style={[styles.description, { color: colors.textMuted }]}>
          positive_score − |negative_score| {">"} 0 → positif, {"<"} 0 → negatif, = 0 → netral. Pada mode
          binary, data netral dikeluarkan dari training/evaluation (tetap ditampilkan jumlahnya).
        </Text>

        <View style={styles.modeRow}>
          {(["binary", "ternary"] as const).map((m) => (
            <PrimaryButton
              key={m}
              label={m === "binary" ? "Binary" : "Ternary"}
              onPress={() => setMode(m)}
              variant={mode === m ? "primary" : "secondary"}
            />
          ))}
        </View>

        <PrimaryButton label="Jalankan Labelisasi" onPress={handleStart} loading={startMutation.isPending} />
      </Card>

      {summary ? (
        <>
          <View style={styles.statsGrid}>
            <StatCard label="Positif" value={summary.positive_count} accentColor={palette.positive} />
            <StatCard label="Negatif" value={summary.negative_count} accentColor={palette.negative} />
            <StatCard label="Netral" value={summary.neutral_count} accentColor={palette.neutral} />
            <StatCard label="Dikeluarkan dari Training" value={summary.excluded_from_training} />
          </View>
          <Badge text={statusLabel(summary.status)} />
        </>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  description: { fontSize: 13, marginBottom: spacing.md },
  modeRow: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.md },
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginBottom: spacing.sm },
});
