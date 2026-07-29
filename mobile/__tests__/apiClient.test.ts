import { AxiosError } from "axios";

import { extractErrorMessage } from "@/lib/api/client";

describe("extractErrorMessage", () => {
  it("extracts message from backend error body", () => {
    const error = new AxiosError("Request failed");
    error.response = {
      data: { error: { code: "VALIDATION_ERROR", message: "Data tidak valid." } },
      status: 422,
      statusText: "Unprocessable Entity",
      headers: {},
      // @ts-expect-error minimal mock config
      config: {},
    };
    expect(extractErrorMessage(error)).toBe("Data tidak valid.");
  });

  it("falls back to axios message when no structured error body", () => {
    const error = new AxiosError("Network Error");
    expect(extractErrorMessage(error)).toBe("Network Error");
  });

  it("handles plain Error instances", () => {
    expect(extractErrorMessage(new Error("Kesalahan biasa"))).toBe("Kesalahan biasa");
  });

  it("returns generic message for unknown error shapes", () => {
    expect(extractErrorMessage("bukan error object")).toBe(
      "Terjadi kesalahan yang tidak diketahui.",
    );
  });
});
