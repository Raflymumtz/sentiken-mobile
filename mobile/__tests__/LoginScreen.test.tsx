import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import type { PropsWithChildren } from "react";

import LoginScreen from "@/app/(auth)/login";

const mockReplace = jest.fn();
jest.mock("expo-router", () => ({
  useRouter: () => ({ replace: mockReplace, push: jest.fn() }),
}));

const mockMutateAsync = jest.fn();
jest.mock("@/lib/hooks/useAuth", () => ({
  useLogin: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

function Wrapper({ children }: PropsWithChildren) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("LoginScreen", () => {
  beforeEach(() => {
    mockMutateAsync.mockReset();
    mockReplace.mockReset();
  });

  it("shows validation errors when submitting empty form", async () => {
    render(<LoginScreen />, { wrapper: Wrapper });

    fireEvent.press(screen.getByRole("button", { name: "Tombol masuk ke aplikasi" }));

    await waitFor(() => {
      expect(screen.getByText("Email wajib diisi")).toBeTruthy();
      expect(screen.getByText("Kata sandi wajib diisi")).toBeTruthy();
    });
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it("submits credentials and navigates to dashboard on success", async () => {
    mockMutateAsync.mockResolvedValueOnce(undefined);
    render(<LoginScreen />, { wrapper: Wrapper });

    fireEvent.changeText(screen.getByLabelText("Email"), "admin@sentiken.local");
    fireEvent.changeText(screen.getByLabelText("Kata Sandi"), "Password123!");
    fireEvent.press(screen.getByRole("button", { name: "Tombol masuk ke aplikasi" }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        email: "admin@sentiken.local",
        password: "Password123!",
      });
      expect(mockReplace).toHaveBeenCalledWith("/(tabs)/dashboard");
    });
  });
});
