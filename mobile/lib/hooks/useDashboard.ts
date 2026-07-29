import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type {
  DashboardSummary,
  FrequentTerm,
  RatingDistributionItem,
  SentimentComparisonItem,
  SentimentTrendPoint,
} from "@/lib/types";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary");
      return data;
    },
  });
}

export function useSentimentComparison() {
  return useQuery({
    queryKey: ["dashboard", "sentiment-comparison"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: SentimentComparisonItem[] }>(
        "/dashboard/sentiment-comparison",
      );
      return data.items;
    },
  });
}

export function useSentimentTrend(granularity: "day" | "week" | "month" = "month") {
  return useQuery({
    queryKey: ["dashboard", "sentiment-trend", granularity],
    queryFn: async () => {
      const { data } = await apiClient.get<{ granularity: string; points: SentimentTrendPoint[] }>(
        "/dashboard/sentiment-trend",
        { params: { granularity } },
      );
      return data.points;
    },
  });
}

export function useRatingDistribution() {
  return useQuery({
    queryKey: ["dashboard", "rating-distribution"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: RatingDistributionItem[] }>(
        "/dashboard/rating-distribution",
      );
      return data.items;
    },
  });
}

export function useFrequentTerms(appSourceId?: string, label?: string) {
  return useQuery({
    queryKey: ["dashboard", "frequent-terms", appSourceId, label],
    queryFn: async () => {
      const { data } = await apiClient.get<{ terms: FrequentTerm[] }>("/dashboard/frequent-terms", {
        params: { app_source_id: appSourceId, label },
      });
      return data.terms;
    },
  });
}
