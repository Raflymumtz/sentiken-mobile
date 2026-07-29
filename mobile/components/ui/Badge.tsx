import { StyleSheet, Text, View } from "react-native";

import { palette } from "@/lib/theme";

interface BadgeProps {
  text: string;
  color?: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "#9CA3AF",
  queued: "#9CA3AF",
  running: palette.primary,
  completed: palette.positive,
  failed: palette.negative,
  cancelled: "#9CA3AF",
  positive: palette.positive,
  negative: palette.negative,
  neutral: palette.neutral,
};

export function Badge({ text, color }: BadgeProps) {
  const resolvedColor = color ?? STATUS_COLORS[text.toLowerCase()] ?? palette.primary;
  return (
    <View style={[styles.badge, { backgroundColor: `${resolvedColor}22`, borderColor: resolvedColor }]}>
      <Text style={[styles.text, { color: resolvedColor }]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: "flex-start",
  },
  text: { fontSize: 12, fontWeight: "600" },
});
