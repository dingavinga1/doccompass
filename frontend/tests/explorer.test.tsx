import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../src/App";
import { renderWithProviders } from "../src/test-utils/render";

describe("Explorer", () => {
  it("renders tree and loads selected section content", async () => {
    const user = userEvent.setup();

    renderWithProviders(<App />, "/explorer/doc-1");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Intro" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Intro" }));

    await waitFor(() => {
      expect(screen.getByText("Introduction content")).toBeInTheDocument();
    });
  });
});
