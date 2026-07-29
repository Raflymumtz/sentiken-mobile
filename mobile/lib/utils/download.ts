import * as FileSystem from "expo-file-system";
import * as Sharing from "expo-sharing";

import { apiClient } from "@/lib/api/client";

/**
 * Mengunduh file dari endpoint backend (butuh header Authorization, sehingga
 * tidak bisa dibuka lewat browser link biasa) lalu membuka dialog share/save
 * bawaan perangkat. `path` relatif terhadap base URL API (mis. "/training-runs/x/export/summary.pdf").
 */
export async function downloadAndShare(path: string, filename: string): Promise<void> {
  const response = await apiClient.get(path, { responseType: "arraybuffer" });
  const base64 = arrayBufferToBase64(response.data as ArrayBuffer);

  const fileUri = `${FileSystem.cacheDirectory}${filename}`;
  await FileSystem.writeAsStringAsync(fileUri, base64, {
    encoding: FileSystem.EncodingType.Base64,
  });

  const canShare = await Sharing.isAvailableAsync();
  if (canShare) {
    await Sharing.shareAsync(fileUri);
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  // eslint-disable-next-line no-undef
  return typeof btoa !== "undefined" ? btoa(binary) : Buffer.from(binary, "binary").toString("base64");
}
