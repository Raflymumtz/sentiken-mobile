import { fireEvent, render, screen } from "@testing-library/react-native";

import { EmptyState } from "@/components/ui/EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="Belum ada dataset" description="Buat dataset baru untuk memulai." />);

    expect(screen.getByText("Belum ada dataset")).toBeTruthy();
    expect(screen.getByText("Buat dataset baru untuk memulai.")).toBeTruthy();
  });

  it("does not render action button when onAction is not provided", () => {
    render(<EmptyState title="Kosong" />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("calls onAction when action button pressed", () => {
    const onAction = jest.fn();
    render(<EmptyState title="Kosong" actionLabel="Tambah" onAction={onAction} />);

    fireEvent.press(screen.getByRole("button", { name: "Tambah" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});
