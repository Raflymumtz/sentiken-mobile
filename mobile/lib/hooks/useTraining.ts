import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, extractErrorMessage } from "@/lib/api/client";
import type { PaginatedResponse, TfidfConfig, KnnConfig, TrainingRun } from "@/lib/types";

export interface TrainInput {
  data_split_id: string;
  tfidf_config?: Partial<TfidfConfig>;
  knn_config?: Partial<KnnConfig>;
}

export interface ExperimentKInput {
  data_split_id: string;
  k_values: number[];
  tfidf_config?: Partial<TfidfConfig>;
  metric?: string;
  weights?: "uniform" | "distance";
  selection_metric?: string;
}

export function useTrainingRuns(datasetId?: string, runType?: "single" | "experiment") {
  return useQuery({
    queryKey: ["training-runs", datasetId, runType],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<TrainingRun>>("/training-runs", {
        params: { dataset_id: datasetId, run_type: runType, page_size: 50 },
      });
      return data;
    },
    enabled: !!datasetId,
  });
}

export function useTrainingRun(id: string | undefined) {
  return useQuery({
    queryKey: ["training-runs", "detail", id],
    queryFn: async () => {
      const { data } = await apiClient.get<TrainingRun>(`/training-runs/${id}`);
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 1500 : false;
    },
  });
}

export function useTrainModel(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TrainInput) => {
      try {
        const { data } = await apiClient.post<TrainingRun>(`/datasets/${datasetId}/train`, payload);
        return data;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["training-runs", datasetId] }),
  });
}

export function useExperimentK(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ExperimentKInput) => {
      try {
        const { data } = await apiClient.post<TrainingRun>(
          `/datasets/${datasetId}/experiment-k`,
          payload,
        );
        return data;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["training-runs", datasetId] }),
  });
}

export function useActivateTrainingRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      try {
        const { data } = await apiClient.post<TrainingRun>(`/training-runs/${id}/activate`, {
          confirm: true,
        });
        return data;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["training-runs"] }),
  });
}
