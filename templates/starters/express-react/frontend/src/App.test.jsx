import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "./App.jsx";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("loads and adds a todo via API", async () => {
    const user = userEvent.setup();
    let todos = [];
    vi.spyOn(global, "fetch").mockImplementation(async (url, init) => {
      if (url === "/api/todos" && (!init || init.method === "GET")) {
        return { ok: true, json: async () => todos };
      }
      if (url === "/api/todos" && init?.method === "POST") {
        const body = JSON.parse(init.body);
        const t = { id: "1", title: body.title, completed: false };
        todos = [...todos, t];
        return { ok: true, json: async () => t };
      }
      return { ok: false, json: async () => ({}) };
    });
    render(<App />);
    await waitFor(() => expect(screen.getByText("No todos yet.")).toBeInTheDocument());
    await user.type(screen.getByPlaceholderText("New todo"), "Buy milk");
    await user.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(screen.getByText("Buy milk")).toBeInTheDocument());
  });
});
