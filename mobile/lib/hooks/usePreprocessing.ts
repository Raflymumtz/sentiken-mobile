import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { PreprocessingResult, PreprocessingStatusResponse } from "@/lib/types";

export function usePreprocessingStatus(datasetId: string | undefined) {
  return useQuery({
    queryKey: ["preprocessing-status", datasetId],
    queryFn: async () => {
      const { data } = await apiClient.get<PreprocessingStatusResponse>(
        `/datasets/${datasetId}/preprocessing-status`,
      );
      return data;
    },
    enabled: !!datasetId,
    refetchInterval: (query) => (query.state.data?.status === "running" ? 1500 : false),
  });
}

export function useStartPreprocessing(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(`/datasets/${datasetId}/preprocess`);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["preprocessing-status", datasetId] }),
  });
}

export function useReviewPreprocessing(reviewId: string | undefined) {
  return useQuery({
    queryKey: ["review-preprocessing", reviewId],
    queryFn: async () => {
      const { data } = await apiClient.get<PreprocessingResult>(`/reviews/${reviewId}/preprocessing`);
      return data;
    },
    enabled: !!reviewId,
    retry: false,
  });
}
