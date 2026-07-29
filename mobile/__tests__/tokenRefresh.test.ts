import axios from "axios";

import { refreshAccessToken } from "@/lib/api/client";
import { useAuthStore } from "@/lib/store/authStore";

jest.mock("axios", () => {
  const actual = jest.requireActual("axios");
  return {
    ...actual,
    post: jest.fn(),
    create: actual.create,
  };
});

describe("refreshAccessToken (penanganan token kedaluwarsa)", () => {
  beforeEach(async () => {
    jest.clearAllMocks();
    await useAuthStore.getState().setTokens("expired-access", "valid-refresh");
  });

  it("returns null immediately when there is no refresh token", async () => {
    await useAuthStore.getState().clearSession();
    const result = await refreshAccessToken();
    expect(result).toBeNull();
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("exchanges refresh token for a new access token and updates the store", async () => {
    (axios.post as jest.Mock).mockResolvedValueOnce({
      data: { access_token: "new-access", refresh_token: "new-refresh" },
    });

    const result = await refreshAccessToken();

    expect(result).toBe("new-access");
    expect(useAuthStore.getState().accessToken).toBe("new-access");
    expect(useAuthStore.getState().refreshToken).toBe("new-refresh");
  });

  it("clears the session when the refresh token itself is rejected (expired/invalid)", async () => {
    (axios.post as jest.Mock).mockRejectedValueOnce({
      response: { status: 401, data: { error: { message: "Refresh token sudah tidak berlaku." } } },
    });

    const result = await refreshAccessToken();

    expect(result).toBeNull();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().refreshToken).toBeNull();
  });
});
