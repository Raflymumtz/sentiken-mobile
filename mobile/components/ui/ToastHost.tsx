import { useEffect } from "react";
import { StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useToastStore } from "@/lib/store/toastStore";
import { palette } from "@/lib/theme";

const VARIANT_COLOR: Record<string, string> = {
  success: palette.positive,
  error: palette.negative,
  info: palette.primary,
};

export function ToastHost() {
  const { message, variant, hide } = useToastStore();

  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(hide, 3000);
    return () => clearTimeout(timer);
  }, [message, hide]);

  if (!message) return null;

  return (
    <SafeAreaView style={styles.wrapper} pointerEvents="none">
      <Text
        style={[styles.toast, { backgroundColor: VARIANT_COLOR[variant] }]}
        accessibilityLiveRegion="polite"
        accessibilityRole="alert"
      >
        {message}
      </Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  wrapper: { position: "absolute", bottom: 0, left: 0, right: 0, alignItems: "center" },
  toast: {
    color: "#FFFFFF",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
    marginBottom: 16,
    fontSize: 13,
    fontWeight: "600",
    overflow: "hidden",
  },
});
