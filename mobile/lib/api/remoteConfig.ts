import * as SecureStore from "expo-secure-store";

// File kecil di GitHub yang menyimpan URL backend saat ini. Karena backend
// berjalan di laptop pribadi lewat Cloudflare Tunnel (URL berubah tiap kali
// tunnel di-restart), aplikasi mengecek file ini di setiap pembukaan aplikasi
// alih-alih menyimpan URL secara permanen di dalam APK -- jadi saat URL
// tunnel berubah, cukup update file ini (tanpa build ulang / instal ulang
// aplikasi di HP).
const REMOTE_CONFIG_URL =
  "https://raw.githubusercontent.com/Raflymumtz/sentiken-mobile/main/mobile/remote-config.json";
const CACHE_KEY = "sentiken_api_base_url";
const FETCH_TIMEOUT_MS = 6000;

const BUILT_IN_FALLBACK_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function fetchRemoteApiUrl(): Promise<string | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    // Query string agar tidak kena cache CDN raw.githubusercontent.com.
    const response = await fetch(`${REMOTE_CONFIG_URL}?t=${Date.now()}`, {
      signal: controller.signal,
    });
    if (!response.ok) return null;
    const data = (await response.json()) as { api_url?: string };
    if (typeof data.api_url === "string" && data.api_url.trim().length > 0) {
      return data.api_url.trim();
    }
    return null;
  } catch {
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

/** Menentukan base URL API: coba ambil dari GitHub dulu, lalu cache lokal, baru fallback bawaan APK. */
export async function resolveApiBaseUrl(): Promise<string> {
  const remoteUrl = await fetchRemoteApiUrl();
  if (remoteUrl) {
    await SecureStore.setItemAsync(CACHE_KEY, remoteUrl).catch(() => undefined);
    return remoteUrl;
  }

  const cached = await SecureStore.getItemAsync(CACHE_KEY).catch(() => null);
  return cached ?? BUILT_IN_FALLBACK_URL;
}
