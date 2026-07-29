import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";

import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette } from "@/lib/theme";

export default function TabsLayout() {
  const { colors } = useThemeColors();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: palette.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ color, size }) => <Ionicons name="home" color={color} size={size} />,
          tabBarAccessibilityLabel: "Tab Dashboard",
        }}
      />
      <Tabs.Screen
        name="dataset"
        options={{
          title: "Dataset",
          tabBarIcon: ({ color, size }) => <Ionicons name="server" color={color} size={size} />,
          tabBarAccessibilityLabel: "Tab Dataset",
        }}
      />
      <Tabs.Screen
        name="proses"
        options={{
          title: "Proses",
          tabBarIcon: ({ color, size }) => <Ionicons name="cog" color={color} size={size} />,
          tabBarAccessibilityLabel: "Tab Proses",
        }}
      />
      <Tabs.Screen
        name="analisis"
        options={{
          title: "Analisis",
          tabBarIcon: ({ color, size }) => <Ionicons name="analytics" color={color} size={size} />,
          tabBarAccessibilityLabel: "Tab Analisis",
        }}
      />
      <Tabs.Screen
        name="pengaturan"
        options={{
          title: "Pengaturan",
          tabBarIcon: ({ color, size }) => <Ionicons name="settings" color={color} size={size} />,
          tabBarAccessibilityLabel: "Tab Pengaturan",
        }}
      />
    </Tabs>
  );
}
