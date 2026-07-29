import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { EvaluationMetrics, PaginatedResponse } from "@/lib/types";

export function useEvaluationMetrics(runId: string | undefined) {
  return useQuery({
    queryKey: ["evaluation-metrics", runId],
    queryFn: async () => {
      const { data } = await apiClient.get<EvaluationMetrics>(`/training-runs/${runId}/metrics`);
      return data;
    },
    enabled: !!runId,
    retry: false,
  });
}

interface PredictionItem {
  id: string;
  review_id: string | null;
  input_text: string;
  actual_label: string | null;
  predicted_label: string;
  is_correct: boolean;
  confidence: number;
  k_used: number;
  neighbors: { review_id: string | null; distance: number; label: string; text: string }[];
  prediction_time_ms: number;
}

export function useRunPredictions(runId: string | undefined, page = 1) {
  return useQuery({
    queryKey: ["run-predictions", runId, page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<PredictionItem>>(
        `/training-runs/${runId}/predictions`,
        { params: { page, page_size: 20 } },
      );
      return data;
    },
    enabled: !!runId,
  });
}
