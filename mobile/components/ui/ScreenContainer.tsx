import type { PropsWithChildren } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { spacing } from "@/lib/theme";

interface ScreenContainerProps extends PropsWithChildren {
  scrollable?: boolean;
  refreshing?: boolean;
  onRefresh?: () => void;
  padded?: boolean;
}

export function ScreenContainer({
  children,
  scrollable = true,
  refreshing = false,
  onRefresh,
  padded = true,
}: ScreenContainerProps) {
  const { colors } = useThemeColors();

  const content = (
    <View style={[styles.content, padded && styles.padded]}>{children}</View>
  );

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]} edges={["top"]}>
      {scrollable ? (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            onRefresh ? <RefreshControl refreshing={refreshing} onRefresh={onRefresh} /> : undefined
          }
        >
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  scrollContent: { flexGrow: 1 },
  content: { flex: 1 },
  padded: { padding: spacing.md },
});
