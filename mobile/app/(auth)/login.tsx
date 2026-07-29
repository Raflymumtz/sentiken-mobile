import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { Controller, useForm } from "react-hook-form";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";
import { z } from "zod";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { TextField } from "@/components/ui/TextField";
import { extractErrorMessage } from "@/lib/api/client";
import { useLogin } from "@/lib/hooks/useAuth";
import { useThemeColors } from "@/lib/hooks/useThemeColors";
import { palette, spacing } from "@/lib/theme";

const loginSchema = z.object({
  email: z.string().min(3, "Email wajib diisi").email("Format email tidak valid"),
  password: z.string().min(1, "Kata sandi wajib diisi"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginScreen() {
  const { colors } = useThemeColors();
  const router = useRouter();
  const loginMutation = useLogin();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: LoginFormValues) => {
    try {
      await loginMutation.mutateAsync(values);
      router.replace("/(tabs)/dashboard");
    } catch {
      // Error ditampilkan lewat loginMutation.error di bawah.
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.header}>
        <Text style={styles.logo}>SENTIKEN</Text>
        <Text style={[styles.tagline, { color: colors.textMuted }]}>
          Analisis Sentimen PLN Mobile & MyPertamina
        </Text>
      </View>

      <View style={styles.form}>
        <Controller
          control={control}
          name="email"
          render={({ field }) => (
            <TextField
              label="Email"
              value={field.value}
              onChangeText={field.onChange}
              onBlur={field.onBlur}
              placeholder="admin@sentiken.local"
              keyboardType="email-address"
              autoCapitalize="none"
              error={errors.email?.message}
            />
          )}
        />
        <Controller
          control={control}
          name="password"
          render={({ field }) => (
            <TextField
              label="Kata Sandi"
              value={field.value}
              onChangeText={field.onChange}
              onBlur={field.onBlur}
              placeholder="Masukkan kata sandi"
              secureTextEntry
              autoCapitalize="none"
              error={errors.password?.message}
            />
          )}
        />

        {loginMutation.isError ? (
          <Text style={styles.errorText}>{extractErrorMessage(loginMutation.error)}</Text>
        ) : null}

        <PrimaryButton
          label="Masuk"
          onPress={handleSubmit(onSubmit)}
          loading={loginMutation.isPending}
          accessibilityLabel="Tombol masuk ke aplikasi"
        />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: spacing.lg },
  header: { alignItems: "center", marginBottom: spacing.xl },
  logo: { fontSize: 28, fontWeight: "800", color: palette.primary, letterSpacing: 1 },
  tagline: { fontSize: 13, marginTop: spacing.xs, textAlign: "center" },
  form: { width: "100%" },
  errorText: { color: palette.negative, marginBottom: spacing.md, fontSize: 13 },
});
