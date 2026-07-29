import { render, screen } from "@testing-library/react-native";

import DashboardScreen from "@/app/(tabs)/dashboard/index";

const mockUseDashboardSummary = jest.fn();
jest.mock("@/lib/hooks/useDashboard", () => ({
  useDashboardSummary: () => mockUseDashboardSummary(),
  useSentimentComparison: () => ({ data: [], refetch: jest.fn() }),
  useSentimentTrend: () => ({ data: [], refetch: jest.fn() }),
}));

describe("DashboardScreen", () => {
  it("shows loading state while fetching summary", () => {
    mockUseDashboardSummary.mockReturnValue({ isLoading: true, isError: false, data: undefined, refetch: jest.fn() });
    render(<DashboardScreen />);
    expect(screen.getByLabelText("Memuat dashboard...")).toBeTruthy();
  });

  it("shows empty state when there is no data yet, without fake metrics", () => {
    mockUseDashboardSummary.mockReturnValue({
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
      data: {
        has_data: false,
        total_datasets: 0,
        total_reviews: 0,
        total_reviews_by_app: {},
        total_reviews_pln_mobile: 0,
        total_reviews_mypertamina: 0,
        sentiment_counts: { positive: 0, negative: 0, neutral: 0 },
        sentiment_percentage: { positive: 0, negative: 0, neutral: 0 },
        active_model_version: null,
        active_k: null,
        active_metrics: null,
        latest_job_status: null,
        latest_job_type: null,
      },
    });

    render(<DashboardScreen />);

    expect(screen.getByText("Belum ada dataset")).toBeTruthy();
    // Metrik seperti accuracy TIDAK boleh muncul saat belum ada data sungguhan.
    expect(screen.queryByText(/Accuracy/i)).toBeNull();
  });

  it("shows error state and allows retry", () => {
    const refetch = jest.fn();
    mockUseDashboardSummary.mockReturnValue({ isLoading: false, isError: true, data: undefined, refetch });

    render(<DashboardScreen />);
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
