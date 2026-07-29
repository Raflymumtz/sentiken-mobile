import { render, screen } from "@testing-library/react-native";

import DatasetListScreen from "@/app/(tabs)/dataset/index";

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

const mockUseDatasets = jest.fn();
jest.mock("@/lib/hooks/useDatasets", () => ({
  useDatasets: () => mockUseDatasets(),
}));

describe("DatasetListScreen", () => {
  it("shows loading state initially", () => {
    mockUseDatasets.mockReturnValue({ isLoading: true, isError: false, data: undefined, refetch: jest.fn() });
    render(<DatasetListScreen />);
    expect(screen.getByLabelText("Memuat dataset...")).toBeTruthy();
  });

  it("shows empty state when there are no datasets", () => {
    mockUseDatasets.mockReturnValue({
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
      data: { items: [], pagination: { page: 1, page_size: 100, total_items: 0, total_pages: 0 } },
    });
    render(<DatasetListScreen />);
    expect(screen.getByText("Belum ada dataset")).toBeTruthy();
  });

  it("renders dataset cards with key fields when data is available", () => {
    mockUseDatasets.mockReturnValue({
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
      data: {
        items: [
          {
            id: "d1",
            name: "Dataset PLN Mobile",
            app_source_id: "a1",
            description: "Dataset uji",
            period_start: null,
            period_end: null,
            preprocessing_status: "pending",
            labeling_status: "pending",
            label_mode: "binary",
            training_status: "pending",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
            review_count: 12,
            app_source: { app_name: "PLN Mobile" },
          },
        ],
        pagination: { page: 1, page_size: 100, total_items: 1, total_pages: 1 },
      },
    });

    render(<DatasetListScreen />);

    expect(screen.getByText("Dataset PLN Mobile")).toBeTruthy();
    expect(screen.getByText(/12 ulasan/)).toBeTruthy();
  });
});
