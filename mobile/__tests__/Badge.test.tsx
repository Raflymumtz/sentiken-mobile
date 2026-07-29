import { render, screen } from "@testing-library/react-native";

import { Badge } from "@/components/ui/Badge";

describe("Badge", () => {
  it("renders the given text", () => {
    render(<Badge text="completed" />);
    expect(screen.getByText("completed")).toBeTruthy();
  });

  it("renders custom text for arbitrary status", () => {
    render(<Badge text="positive" />);
    expect(screen.getByText("positive")).toBeTruthy();
  });
});
