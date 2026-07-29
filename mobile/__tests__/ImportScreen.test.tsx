import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import ImportCsvScreen from "@/app/(tabs)/dataset/[id]/import";

jest.mock("expo-router", () => ({
  useLocalSearchParams: () => ({ id: "dataset-1" }),
  useRouter: () => ({ replace: jest.fn(), push: jest.fn() }),
}));

jest.mock("expo-document-picker", () => ({
  getDocumentAsync: jest.fn(() =>
    Promise.resolve({
      canceled: false,
      assets: [{ uri: "file://sample.csv", name: "sample.csv", mimeType: "text/csv" }],
    }),
  ),
}));

const mockPreviewMutateAsync = jest.fn();
const mockExecuteMutateAsync = jest.fn();
jest.mock("@/lib/hooks/useImports", () => ({
  usePreviewImport: () => ({ mutateAsync: mockPreviewMutateAsync, isPending: false, data: undefined }),
  useExecuteImport: () => ({ mutateAsync: mockExecuteMutateAsync, isPending: false }),
  useImportJob: () => ({ data: undefined }),
}));

describe("ImportCsvScreen (validasi import CSV)", () => {
  beforeEach(() => {
    mockPreviewMutateAsync.mockReset();
    mockExecuteMutateAsync.mockReset();
  });

  it("shows the required-column format hint before any file is picked", () => {
    render(<ImportCsvScreen />);
    expect(screen.getByText(/content \(wajib\)/)).toBeTruthy();
  });

  it("triggers preview when a CSV file is picked", async () => {
    mockPreviewMutateAsync.mockResolvedValueOnce({
      total_rows: 2,
      valid_rows: 1,
      invalid_rows: 1,
      detected_columns: ["content"],
      missing_required_columns: [],
      sample_rows: [],
      upload_token: "token-123",
    });

    render(<ImportCsvScreen />);
    fireEvent.press(screen.getByText("Pilih Berkas CSV"));

    await waitFor(() => {
      expect(mockPreviewMutateAsync).toHaveBeenCalledWith({
        uri: "file://sample.csv",
        name: "sample.csv",
        mimeType: "text/csv",
      });
    });
  });
});
