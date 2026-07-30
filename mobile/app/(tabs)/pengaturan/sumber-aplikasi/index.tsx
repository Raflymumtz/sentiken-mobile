import { useState } from "react";
import { Linking, Pressable, StyleSheet, Switch, Text, View } from "react-native";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import {
  useAppSources,
  useCreateAppSource,
  useDeleteAppSource,
  useUpdateAppSource,
  useValidateAppSource,
} from "@/lib/hooks/useAppSources";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import type { AppSource } from "@/lib/types";

export default function AppSourcesScreen() {
  const { colors } = useThemeColors();
  const showToast = useToastStore((s) => s.show);
  const sourcesQuery = useAppSources();
  const createMutation = useCreateAppSource();

  const [showForm, setShowForm] = useState(false);
  const [appName, setAppName] = useState("");
  const [packageId, setPackageId] = useState("");
  const [description, setDescription] = useState("");

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync({ app_name: appName, package_id: packageId, description });
      setAppName("");
      setPackageId("");
      setDescription("");
      setShowForm(false);
      showToast("Sumber aplikasi ditambahkan.", "success");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  if (sourcesQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat sumber aplikasi..." />
      </ScreenContainer>
    );
  }
  if (sourcesQuery.isError && !sourcesQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => sourcesQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const sources = sourcesQuery.data?.items ?? [];

  return (
    <ScreenContainer>
      <PrimaryButton
        label={showForm ? "Batal" : "+ Tambah Sumber Aplikasi"}
        onPress={() => setShowForm((v) => !v)}
        variant="secondary"
      />

      {showForm ? (
        <Card style={{ marginTop: spacing.sm }}>
          <TextField label="Nama Aplikasi" value={appName} onChangeText={setAppName} placeholder="PLN Mobile" />
          <TextField
            label="Package ID"
            value={packageId}
            onChangeText={setPackageId}
            placeholder="com.icon.pln123"
            autoCapitalize="none"
          />
          <TextField label="Deskripsi (opsional)" value={description} onChangeText={setDescription} multiline />
          <PrimaryButton label="Simpan" onPress={handleCreate} loading={createMutation.isPending} />
        </Card>
      ) : null}

      {sources.length === 0 ? (
        <EmptyState title="Belum ada sumber aplikasi" />
      ) : (
        sources.map((source) => <AppSourceCard key={source.id} source={source} />)
      )}
    </ScreenContainer>
  );
}

function AppSourceCard({ source }: { source: AppSource }) {
  const { colors } = useThemeColors();
  const showToast = useToastStore((s) => s.show);
  const updateMutation = useUpdateAppSource(source.id);
  const deleteMutation = useDeleteAppSource();
  const validateMutation = useValidateAppSource();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleToggleActive = async (value: boolean) => {
    try {
      await updateMutation.mutateAsync({ is_active: value });
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const handleValidate = async () => {
    try {
      const result = await validateMutation.mutateAsync(source.id);
      showToast(result.detail, result.is_valid ? "success" : "error");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(source.id);
      showToast("Sumber aplikasi dihapus.", "success");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    } finally {
      setConfirmDelete(false);
    }
  };

  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={[styles.name, { color: colors.text }]}>{source.app_name}</Text>
        <Switch value={source.is_active} onValueChange={handleToggleActive} accessibilityLabel={`Aktifkan ${source.app_name}`} />
      </View>
      <Text style={[styles.meta, { color: colors.textMuted }]}>{source.package_id}</Text>
      {source.description ? <Text style={[styles.meta, { color: colors.textMuted }]}>{source.description}</Text> : null}
      <View style={styles.badgeRow}>
        <Badge text={source.is_active ? "Aktif" : "Nonaktif"} />
      </View>
      <View style={styles.actionsRow}>
        <PrimaryButton label="Validasi" onPress={handleValidate} variant="secondary" loading={validateMutation.isPending} />
        {source.play_store_url ? (
          <PrimaryButton
            label="Buka Play Store"
            onPress={() => Linking.openURL(source.play_store_url!)}
            variant="secondary"
          />
        ) : null}
        <PrimaryButton label="Hapus" onPress={() => setConfirmDelete(true)} variant="danger" />
      </View>

      <ConfirmDialog
        visible={confirmDelete}
        title="Hapus sumber aplikasi?"
        description={`"${source.app_name}" akan dihapus (soft delete).`}
        destructive
        confirmLabel="Hapus"
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(false)}
      />
    </Card>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  name: { fontSize: 15, fontWeight: "700" },
  meta: { fontSize: 12, marginTop: 2 },
  badgeRow: { flexDirection: "row", marginTop: spacing.sm },
  actionsRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginTop: spacing.sm },
});
