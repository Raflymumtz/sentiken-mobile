import { render, screen } from "@testing-library/react-native";

import EvaluasiDetailScreen from "@/app/(tabs)/analisis/evaluasi/[runId]";

jest.mock("expo-router", () => ({
  useLocalSearchParams: () => ({ runId: "run-1" }),
}));

const mockUseEvaluationMetrics = jest.fn();
jest.mock("@/lib/hooks/useEvaluation", () => ({
  useEvaluationMetrics: () => mockUseEvaluationMetrics(),
}));

jest.mock("@/lib/utils/download", () => ({
  downloadAndShare: jest.fn(),
}));

describe("EvaluasiDetailScreen (tampilan evaluasi)", () => {
  it("shows loading state while fetching metrics", () => {
    mockUseEvaluationMetrics.mockReturnValue({ isLoading: true, isError: false, data: undefined, refetch: jest.fn() });
    render(<EvaluasiDetailScreen />);
    expect(screen.getByLabelText("Memuat hasil evaluasi...")).toBeTruthy();
  });

  it("shows a message when evaluation is not yet available (model belum dilatih)", () => {
    mockUseEvaluationMetrics.mockReturnValue({ isLoading: false, isError: true, data: undefined, refetch: jest.fn() });
    render(<EvaluasiDetailScreen />);
    expect(screen.getByText("Hasil evaluasi belum tersedia.")).toBeTruthy();
  });

  it("renders accuracy, precision, recall, F1-score, and confusion matrix from real metrics", () => {
    mockUseEvaluationMetrics.mockReturnValue({
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
      data: {
        training_run_id: "run-1",
        accuracy: 0.85,
        precision_macro: 0.8,
        recall_macro: 0.82,
        f1_macro: 0.81,
        precision_weighted: 0.86,
        recall_weighted: 0.84,
        f1_weighted: 0.855,
        support: { positive: 10, negative: 10 },
        confusion_matrix: { labels: ["positive", "negative"], matrix: [[9, 1], [2, 8]] },
        classification_report: {},
        warnings: [],
        created_at: "2026-01-01T00:00:00Z",
      },
    });

    render(<EvaluasiDetailScreen />);

    expect(screen.getByText("85.0%")).toBeTruthy();
    expect(screen.getByText("Confusion Matrix")).toBeTruthy();
    expect(screen.getByText("positive: 10")).toBeTruthy();
    expect(screen.getByText("negative: 10")).toBeTruthy();
  });
});
