import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import TrainScreen from "@/app/(tabs)/proses/[datasetId]/train";

jest.mock("expo-router", () => ({
  useLocalSearchParams: () => ({ datasetId: "dataset-1", splitId: undefined }),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

jest.mock("@/lib/hooks/useSplit", () => ({
  useSplits: () => ({
    data: [
      {
        id: "split-1",
        dataset_id: "dataset-1",
        label_mode: "binary",
        train_size: 0.8,
        test_size: 0.2,
        random_state: 42,
        stratify: true,
        train_count: 16,
        test_count: 4,
        class_distribution: { positive: 10, negative: 10 },
        created_at: "2026-01-01T00:00:00Z",
      },
    ],
  }),
}));

const mockTrainMutateAsync = jest.fn();
jest.mock("@/lib/hooks/useTraining", () => ({
  useTrainModel: () => ({ mutateAsync: mockTrainMutateAsync, isPending: false }),
  useActivateTrainingRun: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useTrainingRun: () => ({ data: undefined }),
}));

describe("TrainScreen (form training)", () => {
  beforeEach(() => {
    mockTrainMutateAsync.mockReset();
  });

  it("lists available data splits for selection", () => {
    render(<TrainScreen />);
    expect(screen.getByText(/Train 16 \/ Test 4 \(binary\)/)).toBeTruthy();
  });

  it("submits training with the selected split and default K value", async () => {
    mockTrainMutateAsync.mockResolvedValueOnce({ id: "run-1" });
    render(<TrainScreen />);

    fireEvent.press(screen.getByText(/Train 16 \/ Test 4 \(binary\)/));
    fireEvent.press(screen.getByText("Latih Model"));

    await waitFor(() => {
      expect(mockTrainMutateAsync).toHaveBeenCalledWith({
        data_split_id: "split-1",
        knn_config: { n_neighbors: 3 },
      });
    });
  });
});
