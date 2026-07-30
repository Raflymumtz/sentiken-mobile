import { create } from "zustand";

interface ConnectivityState {
  /** false berarti request terakhir ke backend gagal karena jaringan/timeout
   * (bukan sekadar error 4xx/5xx dari server, yang berarti backend masih
   * terjangkau). Dipakai untuk menampilkan OfflineBanner walau access token
   * masih tersimpan & belum kedaluwarsa. */
  isBackendReachable: boolean;
  setBackendReachable: (reachable: boolean) => void;
}

export const useConnectivityStore = create<ConnectivityState>((set) => ({
  isBackendReachable: true,
  setBackendReachable: (reachable) => set({ isBackendReachable: reachable }),
}));
