import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient, extractErrorMessage } from "@/lib/api/client";
import type { PaginatedResponse, SinglePredictionResult } from "@/lib/types";

export function usePredictSingle() {
  return useMutation({
    mutationFn: async (payload: { text: string; training_run_id?: string }) => {
      try {
        const { data } = await apiClient.post<SinglePredictionResult>("/predictions/single", payload);
        return data;
      } catch (error) {
        throw new Error(extractErrorMessage(error));
      }
    },
  });
}

interface PredictionHistoryItem {
  id: string;
  input_text: string;
  final_text: string;
  predicted_label: string;
  confidence: number;
  k_used: number;
  training_run_id: string;
  created_at: string;
}

export function usePredictionHistory(page = 1) {
  return useQuery({
    queryKey: ["prediction-history", page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<PredictionHistoryItem>>(
        "/predictions/history",
        { params: { page, page_size: 20 } },
      );
      return data;
    },
  });
}
