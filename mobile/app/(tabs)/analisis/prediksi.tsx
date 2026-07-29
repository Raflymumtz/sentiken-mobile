import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import { usePredictSingle } from "@/lib/hooks/usePredictions";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { labelText, spacing } from "@/lib/theme";

export default function PrediksiScreen() {
  const { colors } = useThemeColors();
  const [text, setText] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const predictMutation = usePredictSingle();

  const handlePredict = async () => {
    setErrorMessage(null);
    if (!text.trim()) {
      setErrorMessage("Masukkan teks ulasan terlebih dahulu.");
      return;
    }
    try {
      await predictMutation.mutateAsync({ text });
    } catch (error) {
      setErrorMessage(extractErrorMessage(error));
    }
  };

  const result = predictMutation.data;

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Prediksi Satu Teks</Text>
        <TextField
          label="Teks Ulasan"
          value={text}
          onChangeText={setText}
          placeholder="Masukkan teks ulasan yang ingin diprediksi sentimennya..."
          multiline
        />
        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
        <PrimaryButton label="Prediksi" onPress={handlePredict} loading={predictMutation.isPending} />
      </Card>

      {result ? (
        <Card>
          <Text style={[styles.title, { color: colors.text }]}>Hasil Prediksi</Text>
          <Badge text={labelText(result.predicted_label)} />
          <Text style={[styles.meta, { color: colors.textMuted }]}>
            Confidence: {(result.confidence * 100).toFixed(0)}% · K={result.k_used} · model{" "}
            {result.model_version}
          </Text>
          <Text style={[styles.subheading, { color: colors.text }]}>Teks Final (setelah preprocessing)</Text>
          <Text style={[styles.meta, { color: colors.textMuted }]}>{result.final_text}</Text>

          <Text style={[styles.subheading, { color: colors.text }]}>Tetangga Terdekat</Text>
          {result.neighbors.map((n, idx) => (
            <View key={idx} style={styles.neighborRow}>
              <Text style={[styles.neighborText, { color: colors.text }]} numberOfLines={2}>
                {idx + 1}. {n.text}
              </Text>
              <Text style={[styles.neighborMeta, { color: colors.textMuted }]}>
                {labelText(n.label)} · jarak {n.distance.toFixed(4)}
              </Text>
            </View>
          ))}
        </Card>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  meta: { fontSize: 12, marginTop: spacing.xs },
  subheading: { fontSize: 13, fontWeight: "700", marginTop: spacing.md, marginBottom: spacing.xs },
  neighborRow: { marginBottom: spacing.xs },
  neighborText: { fontSize: 12 },
  neighborMeta: { fontSize: 11 },
  errorText: { color: "#DC2626", fontSize: 12, marginBottom: spacing.sm },
});
