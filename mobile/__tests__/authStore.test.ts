import * as SecureStore from "expo-secure-store";

import { useAuthStore } from "@/lib/store/authStore";

describe("authStore", () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isHydrated: false });
    jest.clearAllMocks();
  });

  it("starts with no session", () => {
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
  });

  it("persists tokens to SecureStore on setSession and updates state", async () => {
    await useAuthStore.getState().setSession("access-123", "refresh-456", {
      id: "u1",
      email: "admin@sentiken.local",
      full_name: "Admin",
      role: "admin",
      is_active: true,
    });

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith("sentiken_access_token", "access-123");
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith("sentiken_refresh_token", "refresh-456");
    expect(useAuthStore.getState().accessToken).toBe("access-123");
    expect(useAuthStore.getState().user?.email).toBe("admin@sentiken.local");
  });

  it("clears tokens from SecureStore and state on clearSession", async () => {
    await useAuthStore.getState().setTokens("a", "b");
    await useAuthStore.getState().clearSession();

    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith("sentiken_access_token");
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith("sentiken_refresh_token");
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("hydrate reads tokens from SecureStore and marks hydrated", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockImplementation((key: string) =>
      Promise.resolve(key === "sentiken_access_token" ? "stored-access" : "stored-refresh"),
    );

    await useAuthStore.getState().hydrate();

    expect(useAuthStore.getState().accessToken).toBe("stored-access");
    expect(useAuthStore.getState().refreshToken).toBe("stored-refresh");
    expect(useAuthStore.getState().isHydrated).toBe(true);
  });
});
