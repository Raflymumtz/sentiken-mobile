import { create } from "zustand";

export type ThemePreference = "light" | "dark" | "system";

interface SettingsState {
  themePreference: ThemePreference;
  setThemePreference: (value: ThemePreference) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  themePreference: "system",
  setThemePreference: (value) => set({ themePreference: value }),
}));
