import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { z } from "zod";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import { useAppSources } from "@/lib/hooks/useAppSources";
import { useCreateDataset } from "@/lib/hooks/useDatasets";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

const schema = z.object({
  name: z.string().min(1, "Nama dataset wajib diisi"),
  app_source_id: z.string().min(1, "Pilih sumber aplikasi"),
  description: z.string().optional(),
  period_start: z.string().regex(dateRegex, "Format: YYYY-MM-DD").or(z.literal("")).optional(),
  period_end: z.string().regex(dateRegex, "Format: YYYY-MM-DD").or(z.literal("")).optional(),
  label_mode: z.enum(["binary", "ternary"]),
});

type FormValues = z.infer<typeof schema>;

export default function CreateDatasetScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();
  const appSourcesQuery = useAppSources({ is_active: true });
  const createDataset = useCreateDataset();
  const showToast = useToastStore((s) => s.show);

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", app_source_id: "", description: "", period_start: "", period_end: "", label_mode: "binary" },
  });

  const selectedAppSourceId = watch("app_source_id");

  const onSubmit = async (values: FormValues) => {
    try {
      const dataset = await createDataset.mutateAsync({
        name: values.name,
        app_source_id: values.app_source_id,
        description: values.description || undefined,
        period_start: values.period_start || undefined,
        period_end: values.period_end || undefined,
        label_mode: values.label_mode,
      });
      showToast("Dataset berhasil dibuat.", "success");
      router.replace(`/(tabs)/dataset/${dataset.id}`);
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const appSources = appSourcesQuery.data?.items ?? [];

  return (
    <ScreenContainer>
      <Controller
        control={control}
        name="name"
        render={({ field }) => (
          <TextField
            label="Nama Dataset"
            value={field.value}
            onChangeText={field.onChange}
            placeholder="mis. PLN Mobile - Semester 1 2026"
            error={errors.name?.message}
          />
        )}
      />

      <Text style={[styles.label, { color: colors.text }]}>Sumber Aplikasi</Text>
      {appSources.length === 0 ? (
        <EmptyState
          title="Belum ada sumber aplikasi"
          description="Tambahkan sumber aplikasi terlebih dahulu di menu Pengaturan."
          actionLabel="Ke Pengaturan"
          onAction={() => router.push("/(tabs)/pengaturan/sumber-aplikasi")}
        />
      ) : (
        <Card>
          {appSources.map((source) => (
            <Pressable
              key={source.id}
              onPress={() => setValue("app_source_id", source.id, { shouldValidate: true })}
              accessibilityRole="radio"
              accessibilityState={{ selected: selectedAppSourceId === source.id }}
              style={styles.optionRow}
            >
              <View
                style={[
                  styles.radio,
                  { borderColor: colors.border },
                  selectedAppSourceId === source.id && styles.radioSelected,
                ]}
              />
              <Text style={{ color: colors.text }}>{source.app_name}</Text>
            </Pressable>
          ))}
        </Card>
      )}
      {errors.app_source_id ? <Text style={styles.error}>{errors.app_source_id.message}</Text> : null}

      <Controller
        control={control}
        name="description"
        render={({ field }) => (
          <TextField
            label="Deskripsi (opsional)"
            value={field.value ?? ""}
            onChangeText={field.onChange}
            multiline
          />
        )}
      />

      <Controller
        control={control}
        name="period_start"
        render={({ field }) => (
          <TextField
            label="Periode Mulai (YYYY-MM-DD, opsional)"
            value={field.value ?? ""}
            onChangeText={field.onChange}
            placeholder="2026-01-01"
            error={errors.period_start?.message}
          />
        )}
      />
      <Controller
        control={control}
        name="period_end"
        render={({ field }) => (
          <TextField
            label="Periode Akhir (YYYY-MM-DD, opsional)"
            value={field.value ?? ""}
            onChangeText={field.onChange}
            placeholder="2026-06-30"
            error={errors.period_end?.message}
          />
        )}
      />

      <Text style={[styles.label, { color: colors.text }]}>Mode Label</Text>
      <View style={styles.modeRow}>
        {(["binary", "ternary"] as const).map((mode) => (
          <Pressable
            key={mode}
            onPress={() => setValue("label_mode", mode)}
            style={[
              styles.modeOption,
              { borderColor: colors.border },
              watch("label_mode") === mode && styles.modeOptionSelected,
            ]}
            accessibilityRole="radio"
            accessibilityState={{ selected: watch("label_mode") === mode }}
          >
            <Text style={{ color: colors.text }}>{mode === "binary" ? "Binary" : "Ternary"}</Text>
          </Pressable>
        ))}
      </View>

      <PrimaryButton
        label="Simpan Dataset"
        onPress={handleSubmit(onSubmit)}
        loading={createDataset.isPending}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 13, fontWeight: "600", marginBottom: spacing.xs },
  optionRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.xs },
  radio: { width: 18, height: 18, borderRadius: 9, borderWidth: 2 },
  radioSelected: { backgroundColor: "#1D4ED8", borderColor: "#1D4ED8" },
  error: { color: "#DC2626", fontSize: 12, marginBottom: spacing.md },
  modeRow: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.lg },
  modeOption: { flex: 1, borderWidth: 1, borderRadius: 8, padding: spacing.sm, alignItems: "center" },
  modeOptionSelected: { borderColor: "#1D4ED8", borderWidth: 2 },
});
