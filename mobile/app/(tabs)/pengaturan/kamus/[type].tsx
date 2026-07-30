import * as DocumentPicker from "expo-document-picker";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import {
  useCreateDictionaryEntry,
  useDeleteDictionaryEntry,
  useDictionaryEntries,
  useImportDictionary,
} from "@/lib/hooks/useDictionaries";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import type { DictionaryType } from "@/lib/types";
import { downloadAndShare } from "@/lib/utils/download";

const TYPE_LABELS: Record<DictionaryType, string> = {
  positive: "Kamus Positif",
  negative: "Kamus Negatif",
  normalization: "Kamus Normalisasi",
  stopwords: "Kamus Stopword",
};

export default function DictionaryScreen() {
  const { type } = useLocalSearchParams<{ type: DictionaryType }>();
  const { colors } = useThemeColors();
  const showToast = useToastStore((s) => s.show);

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [word, setWord] = useState("");
  const [weight, setWeight] = useState("1.0");
  const [formalWord, setFormalWord] = useState("");

  const entriesQuery = useDictionaryEntries(type, search, page);
  const createMutation = useCreateDictionaryEntry(type);
  const deleteMutation = useDeleteDictionaryEntry(type);
  const importMutation = useImportDictionary(type);

  const handleCreate = async () => {
    try {
      const payload: Record<string, string | number> =
        type === "normalization"
          ? { informal_word: word, formal_word: formalWord }
          : type === "stopwords"
            ? { word }
            : { word, weight: Number(weight) };
      await createMutation.mutateAsync(payload);
      setWord("");
      setFormalWord("");
      setWeight("1.0");
      showToast("Entri kamus ditambahkan.", "success");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const handleImport = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: "text/csv", copyToCacheDirectory: true });
    if (result.canceled || !result.assets?.[0]) return;
    const asset = result.assets[0];
    try {
      const report = await importMutation.mutateAsync({ uri: asset.uri, name: asset.name, mimeType: asset.mimeType });
      showToast(`Import selesai: ${report.inserted} baru, ${report.duplicates_skipped} duplikat.`, "success");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  if (entriesQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat kamus..." />
      </ScreenContainer>
    );
  }
  if (entriesQuery.isError && !entriesQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => entriesQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const entries = entriesQuery.data?.items ?? [];
  const pagination = entriesQuery.data?.pagination;

  return (
    <ScreenContainer>
      <Text style={[styles.title, { color: colors.text }]}>{TYPE_LABELS[type]}</Text>

      <Card>
        {type === "normalization" ? (
          <>
            <TextField label="Kata Tidak Baku" value={word} onChangeText={setWord} />
            <TextField label="Kata Baku" value={formalWord} onChangeText={setFormalWord} />
          </>
        ) : (
          <TextField label="Kata" value={word} onChangeText={setWord} autoCapitalize="none" />
        )}
        {type === "positive" || type === "negative" ? (
          <TextField label="Bobot" value={weight} onChangeText={setWeight} keyboardType="decimal-pad" />
        ) : null}
        <View style={styles.buttonRow}>
          <View style={styles.buttonFlex}>
            <PrimaryButton label="Tambah" onPress={handleCreate} loading={createMutation.isPending} />
          </View>
          <View style={styles.buttonFlex}>
            <PrimaryButton label="Import CSV" onPress={handleImport} variant="secondary" loading={importMutation.isPending} />
          </View>
        </View>
        <PrimaryButton
          label="Export CSV"
          variant="secondary"
          onPress={() => downloadAndShare(`/dictionaries/${type}/export`, `kamus_${type}.csv`)}
        />
      </Card>

      <TextField
        label="Cari"
        value={search}
        onChangeText={(v) => {
          setSearch(v);
          setPage(1);
        }}
        placeholder="Cari kata..."
      />

      {entries.length === 0 ? (
        <EmptyState title="Belum ada entri kamus" />
      ) : (
        entries.map((entry) => (
          <Card key={entry.id}>
            <View style={styles.entryRow}>
              <Text style={{ color: colors.text, fontSize: 14 }}>
                {type === "normalization" ? `${entry.informal_word} → ${entry.formal_word}` : entry.word}
                {entry.weight !== undefined ? ` (bobot: ${entry.weight})` : ""}
              </Text>
              <PrimaryButton
                label="Hapus"
                variant="danger"
                onPress={() => deleteMutation.mutate(entry.id)}
              />
            </View>
          </Card>
        ))
      )}

      {pagination && pagination.total_pages > page ? (
        <PrimaryButton label="Muat Lebih Banyak" onPress={() => setPage((p) => p + 1)} variant="secondary" />
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 18, fontWeight: "700", marginBottom: spacing.md },
  buttonRow: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.sm },
  buttonFlex: { flex: 1 },
  entryRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
});
