import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import CollectionScreen from "@/app/(tabs)/proses/[datasetId]/collection";

jest.mock("expo-router", () => ({
  useLocalSearchParams: () => ({ datasetId: "dataset-1" }),
}));

jest.mock("@/lib/hooks/useDatasets", () => ({
  useDataset: () => ({
    isLoading: false,
    isError: false,
    data: {
      id: "dataset-1",
      app_source_id: "source-1",
      app_source: { app_name: "PLN Mobile", package_id: "com.icon.pln" },
    },
    refetch: jest.fn(),
  }),
}));

const mockCreateJob = jest.fn();
jest.mock("@/lib/hooks/useCollectionJobs", () => ({
  useCreateCollectionJob: () => ({ mutateAsync: mockCreateJob, isPending: false }),
  useCancelCollectionJob: () => ({ mutate: jest.fn(), isPending: false }),
  useCollectionJob: () => ({ data: undefined }),
}));

describe("CollectionScreen (form Pengumpulan Data)", () => {
  beforeEach(() => {
    mockCreateJob.mockReset();
  });

  it("shows dataset source info from the linked app source", () => {
    render(<CollectionScreen />);
    expect(screen.getByText(/PLN Mobile \(com\.icon\.pln\)/)).toBeTruthy();
  });

  it("submits with default form values (max_reviews, language, country, sort_order)", async () => {
    mockCreateJob.mockResolvedValueOnce({ id: "job-1" });
    render(<CollectionScreen />);

    fireEvent.press(screen.getByText("Mulai Pengumpulan Data"));

    await waitFor(() => {
      expect(mockCreateJob).toHaveBeenCalledWith(
        expect.objectContaining({
          app_source_id: "source-1",
          dataset_id: "dataset-1",
          max_reviews: 1000,
          language: "id",
          country: "id",
          sort_order: "newest",
        }),
      );
    });
  });
});
