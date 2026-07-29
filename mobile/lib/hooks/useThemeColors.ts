import { useColorScheme } from "react-native";

import { useSettingsStore } from "@/lib/store/settingsStore";
import { getThemeColors } from "@/lib/theme";

export function useThemeColors() {
  const systemScheme = useColorScheme();
  const preference = useSettingsStore((s) => s.themePreference);
  const effectiveScheme = preference === "system" ? systemScheme : preference;
  return { colors: getThemeColors(effectiveScheme), scheme: effectiveScheme };
}
