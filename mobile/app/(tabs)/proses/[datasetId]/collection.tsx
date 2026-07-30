import { zodResolver } from "@hookform/resolvers/zod";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { StyleSheet, Text, View } from "react-native";
import { z } from "zod";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import {
  useCancelCollectionJob,
  useCollectionJob,
  useCreateCollectionJob,
} from "@/lib/hooks/useCollectionJobs";
import { useDataset } from "@/lib/hooks/useDatasets";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { useToastStore } from "@/lib/store/toastStore";
import { spacing } from "@/lib/theme";
import { formatDateTime, statusLabel } from "@/lib/utils/format";

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

const schema = z.object({
  period_start: z.string().regex(dateRegex).or(z.literal("")).optional(),
  period_end: z.string().regex(dateRegex).or(z.literal("")).optional(),
  max_reviews: z.string().regex(/^\d+$/, "Harus berupa angka"),
  language: z.string().min(2),
  country: z.string().min(2),
  sort_order: z.enum(["newest", "rating", "relevance"]),
});

type FormValues = z.infer<typeof schema>;

export default function CollectionScreen() {
  const { datasetId } = useLocalSearchParams<{ datasetId: string }>();
  const { colors } = useThemeColors();
  const showToast = useToastStore((s) => s.show);
  const [activeJobId, setActiveJobId] = useState<string | undefined>(undefined);

  const datasetQuery = useDataset(datasetId);
  const createJob = useCreateCollectionJob();
  const cancelJob = useCancelCollectionJob();
  const jobQuery = useCollectionJob(activeJobId);

  const { control, handleSubmit, setValue, watch } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      period_start: "",
      period_end: "",
      max_reviews: "1000",
      language: "id",
      country: "id",
      sort_order: "newest",
    },
  });

  if (datasetQuery.isLoading) {
    return (
      <ScreenContainer>
        <LoadingState label="Memuat dataset..." />
      </ScreenContainer>
    );
  }
  if (datasetQuery.isError && !datasetQuery.data) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={() => datasetQuery.refetch()} />
      </ScreenContainer>
    );
  }

  const dataset = datasetQuery.data;
  if (!dataset) return null;

  const onSubmit = async (values: FormValues) => {
    try {
      const job = await createJob.mutateAsync({
        app_source_id: dataset.app_source_id,
        dataset_id: dataset.id,
        period_start: values.period_start || undefined,
        period_end: values.period_end || undefined,
        max_reviews: Number(values.max_reviews),
        language: values.language,
        country: values.country,
        sort_order: values.sort_order,
      });
      setActiveJobId(job.id);
      showToast("Job pengumpulan data dimulai.", "info");
    } catch (error) {
      showToast(extractErrorMessage(error), "error");
    }
  };

  const job = jobQuery.data;
  const sortOptions: FormValues["sort_order"][] = ["newest", "rating", "relevance"];

  return (
    <ScreenContainer>
      <Card>
        <Text style={[styles.title, { color: colors.text }]}>Pengumpulan Ulasan Google Play Store</Text>
        <Text style={[styles.meta, { color: colors.textMuted }]}>
          Sumber: {dataset.app_source?.app_name ?? "-"} ({dataset.app_source?.package_id ?? "-"})
        </Text>

        <Controller
          control={control}
          name="period_start"
          render={({ field }) => (
            <TextField
              label="Tanggal Awal (YYYY-MM-DD, opsional — default 6 bulan terakhir)"
              value={field.value ?? ""}
              onChangeText={field.onChange}
              placeholder="2026-01-01"
            />
          )}
        />
        <Controller
          control={control}
          name="period_end"
          render={({ field }) => (
            <TextField
              label="Tanggal Akhir (YYYY-MM-DD, opsional)"
              value={field.value ?? ""}
              onChangeText={field.onChange}
              placeholder="2026-06-30"
            />
          )}
        />
        <Controller
          control={control}
          name="max_reviews"
          render={({ field }) => (
            <TextField
              label="Maksimal Ulasan"
              value={field.value}
              onChangeText={field.onChange}
              keyboardType="numeric"
            />
          )}
        />
        <Controller
          control={control}
          name="language"
          render={({ field }) => (
            <TextField label="Bahasa" value={field.value} onChangeText={field.onChange} placeholder="id" />
          )}
        />
        <Controller
          control={control}
          name="country"
          render={({ field }) => (
            <TextField label="Negara" value={field.value} onChangeText={field.onChange} placeholder="id" />
          )}
        />

        <Text style={[styles.label, { color: colors.text }]}>Urutan</Text>
        <View style={styles.sortRow}>
          {sortOptions.map((opt) => (
            <PrimaryButton
              key={opt}
              label={opt}
              onPress={() => setValue("sort_order", opt)}
              variant={watch("sort_order") === opt ? "primary" : "secondary"}
            />
          ))}
        </View>

        <PrimaryButton label="Mulai Pengumpulan Data" onPress={handleSubmit(onSubmit)} loading={createJob.isPending} />
      </Card>

      {job ? (
        <Card>
          <Text style={[styles.title, { color: colors.text }]}>Status Job</Text>
          <View style={styles.badgeRow}>
            <Badge text={statusLabel(job.status)} />
          </View>
          <ProgressBar percent={job.progress_percent} />
          <Text style={[styles.meta, { color: colors.textMuted }]}>
            Ditemukan: {job.found_count} · Baru: {job.new_count} · Duplikat: {job.duplicate_count}
          </Text>
          <Text style={[styles.meta, { color: colors.textMuted }]}>
            Mulai: {formatDateTime(job.started_at)} · Selesai: {formatDateTime(job.finished_at)}
          </Text>
          {job.error_message ? <Text style={styles.errorText}>{job.error_message}</Text> : null}
          {job.status === "queued" || job.status === "running" ? (
            <PrimaryButton
              label="Batalkan"
              onPress={() => cancelJob.mutate(job.id)}
              variant="danger"
              loading={cancelJob.isPending}
            />
          ) : null}
        </Card>
      ) : null}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: "700", marginBottom: spacing.sm },
  meta: { fontSize: 12, marginTop: spacing.xs },
  label: { fontSize: 13, fontWeight: "600", marginBottom: spacing.xs },
  sortRow: { flexDirection: "row", gap: spacing.xs, marginBottom: spacing.md, flexWrap: "wrap" },
  badgeRow: { flexDirection: "row", marginBottom: spacing.sm },
  errorText: { color: "#DC2626", fontSize: 12, marginTop: spacing.sm },
});
