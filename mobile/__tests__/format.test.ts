import { formatDate, formatPercent, statusLabel } from "@/lib/utils/format";

describe("format utils", () => {
  it("formats ISO date string to Indonesian locale", () => {
    const result = formatDate("2026-03-15");
    expect(result).not.toBe("-");
    expect(result).not.toBe("2026-03-15");
  });

  it("returns dash for null/undefined date", () => {
    expect(formatDate(null)).toBe("-");
    expect(formatDate(undefined)).toBe("-");
  });

  it("translates status codes to Indonesian labels", () => {
    expect(statusLabel("running")).toBe("Berjalan");
    expect(statusLabel("completed")).toBe("Selesai");
    expect(statusLabel("failed")).toBe("Gagal");
  });

  it("passes through unknown status unchanged", () => {
    expect(statusLabel("unknown_status")).toBe("unknown_status");
  });

  it("formats percent with default one decimal", () => {
    expect(formatPercent(42.567)).toBe("42.6%");
  });

  it("formats percent with custom decimals", () => {
    expect(formatPercent(42.567, 2)).toBe("42.57%");
  });
});
