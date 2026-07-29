import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { Dataset, DatasetSummary, PaginatedResponse, Review } from "@/lib/types";

export interface DatasetInput {
  name: string;
  app_source_id: string;
  description?: string;
  period_start?: string;
  period_end?: string;
  label_mode?: "binary" | "ternary";
}

export function useDatasets(appSourceId?: string) {
  return useQuery({
    queryKey: ["datasets", appSourceId],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<Dataset>>("/datasets", {
        params: { app_source_id: appSourceId, page_size: 100 },
      });
      return data;
    },
  });
}

export function useDataset(id: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "detail", id],
    queryFn: async () => {
      const { data } = await apiClient.get<Dataset>(`/datasets/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useDatasetSummary(id: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "summary", id],
    queryFn: async () => {
      const { data } = await apiClient.get<DatasetSummary>(`/datasets/${id}/summary`);
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data;
      return status &&
        (status.preprocessing_status === "running" ||
          status.labeling_status === "running" ||
          status.training_status === "running")
        ? 2000
        : false;
    },
  });
}

export function useDatasetReviews(
  id: string | undefined,
  filters: Record<string, string | number | undefined> = {},
  page = 1,
) {
  return useQuery({
    queryKey: ["datasets", "reviews", id, filters, page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<Review>>(`/datasets/${id}/reviews`, {
        params: { ...filters, page, page_size: 20 },
      });
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: DatasetInput) => {
      const { data } = await apiClient.post<Dataset>("/datasets", payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

export function useUpdateDataset(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<DatasetInput>) => {
      const { data } = await apiClient.put<Dataset>(`/datasets/${id}`, payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

export function useDeleteDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/datasets/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

export function datasetExportUrl(datasetId: string, kind: "raw" | "preprocessing" | "labeling") {
  return `/datasets/${datasetId}/export?kind=${kind}`;
}
