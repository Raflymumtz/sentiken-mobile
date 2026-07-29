import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, extractErrorMessage } from "@/lib/api/client";
import type { DataSplit } from "@/lib/types";

export interface SplitInput {
  train_size: number;
  test_size: number;
  random_state: number;
  stratify: boolean;
  label_mode: "binary" | "ternary";
}

export function useSplits(datasetId: string | undefined) {
  return useQuery({
    queryKey: ["splits", datasetId],
    queryFn: async () => {
      const { data } = await apiClient.get<DataSplit[]>(`/datasets/${datasetId}/splits`);
      return data;
    },
    enabled: !!datasetId,
  });
}

export function useCreateSplit(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SplitInput) => {
      try {
        const { data } = await apiClient.post<DataSplit>(`/datasets/${datasetId}/split`, payload);
        return data;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["splits", datasetId] }),
  });
}
