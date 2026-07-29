import { StyleSheet, View } from "react-native";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette } from "@/lib/theme";

export function ProgressBar({ percent }: { percent: number }) {
  const { colors } = useThemeColors();
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <View
      style={[styles.track, { backgroundColor: colors.border }]}
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max: 100, now: clamped }}
    >
      <View style={[styles.fill, { width: `${clamped}%` }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: { height: 8, borderRadius: 4, overflow: "hidden", width: "100%" },
  fill: { height: "100%", backgroundColor: palette.primary },
});
