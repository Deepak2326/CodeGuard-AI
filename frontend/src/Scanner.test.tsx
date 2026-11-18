import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, it, expect, beforeEach } from "vitest";
import Scanner from "./Scanner";
import { api } from "./api";
import type { Prediction } from "./types";
vi.mock("./CodeEditor", () => ({
  default: ({
    code,
    onChange,
    disabled,
  }: {
    code: string;
    onChange: (v: string) => void;
    disabled: boolean;
  }) => (
    <textarea
      aria-label="Source code editor"
      value={code}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
    />
  ),
}));
vi.mock("./api", () => ({
  api: { predict: vi.fn() },
  errorMessage: (e: Error) => e.message,
}));
const response: Prediction = {
  predicted_category: "SQL Injection",
  class_id: 0,
  leading_class_id: 0,
  confidence: 0.8,
  probabilities: [{ class_id: 0, category: "SQL Injection", probability: 0.8 }],
  uncertain: false,
  uncertainty_reasons: [],
  explanation: {
    id: 0,
    name: "SQL Injection",
    cwe: ["CWE-89"],
    severity: "High (heuristic)",
    description: "Untrusted query input.",
    root_cause: "Concatenation",
    impact: "Data loss",
    mitigation: "Use parameterized queries.",
    guidance: "Review context.",
  },
  severity: "High (heuristic)",
  severity_note: "Context dependent.",
  localization: "Function-level only.",
  confidence_note: "Model estimate.",
  model_version: "test",
  history_id: null,
};
beforeEach(() => vi.clearAllMocks());
const setup = () =>
  render(<Scanner languages={["c", "cpp", "java"]} onScan={vi.fn()} />);
it("accepts editor input and language selection, submits actual values, renders response", async () => {
  vi.mocked(api.predict).mockResolvedValue(response);
  setup();
  const user = userEvent.setup();
  expect(screen.getByRole("button", { name: /Analyze code/ })).toBeDisabled();
  await user.type(screen.getByLabelText("Source code editor"), "source text");
  await user.selectOptions(screen.getByLabelText("Language"), "java");
  await user.click(screen.getByRole("button", { name: /Analyze code/ }));
  await screen.findByRole("heading", { name: "SQL Injection" });
  expect(api.predict).toHaveBeenCalledWith("source text", "java");
  expect(screen.getAllByText("80.0%")[0]).toBeInTheDocument();
  expect(screen.getByText("Use parameterized queries.")).toBeInTheDocument();
});
it("shows pending state and no result before the API resolves", async () => {
  let resolve!: (v: Prediction) => void;
  vi.mocked(api.predict).mockReturnValue(new Promise((r) => (resolve = r)));
  setup();
  fireEvent.change(screen.getByLabelText("Source code editor"), {
    target: { value: "test code" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Analyze code/ }));
  expect(await screen.findByText("Inspecting your code")).toBeInTheDocument();
  expect(screen.queryByText("SQL Injection")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Language")).toBeDisabled();
  resolve(response);
  await screen.findByRole("heading", { name: "SQL Injection" });
});
it("shows an API error and allows retry", async () => {
  vi.mocked(api.predict).mockRejectedValue(new Error("Model unavailable"));
  setup();
  fireEvent.change(screen.getByLabelText("Source code editor"), {
    target: { value: "test code" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Analyze code/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Model unavailable",
  );
  expect(screen.getByRole("button", { name: /Analyze code/ })).toBeEnabled();
});
it("clears stale results when the code changes", async () => {
  vi.mocked(api.predict).mockResolvedValue(response);
  setup();
  fireEvent.click(screen.getByText("Load example"));
  fireEvent.click(screen.getByRole("button", { name: /Analyze code/ }));
  await screen.findByRole("heading", { name: "SQL Injection" });
  fireEvent.click(screen.getByLabelText("Clear editor"));
  expect(screen.queryByText("SQL Injection")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Source code editor")).toHaveValue("");
});
it("rejects oversized uploads", async () => {
  setup();
  const file = new File(["x".repeat(20001)], "large.c", { type: "text/plain" });
  fireEvent.change(screen.getByLabelText("Upload source file"), {
    target: { files: [file] },
  });
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "smaller than 20 KB",
  );
});
it("loads a supported source file and updates its language", async () => {
  setup();
  const file = new File(["class Example {}"], "Example.java", {
    type: "text/plain",
  });
  Object.defineProperty(file, "text", {
    value: async () => "class Example {}",
  });
  fireEvent.change(screen.getByLabelText("Upload source file"), {
    target: { files: [file] },
  });
  await waitFor(() =>
    expect(screen.getByLabelText("Source code editor")).toHaveValue(
      "class Example {}",
    ),
  );
  expect(screen.getByLabelText("Language")).toHaveValue("java");
});
it("shows abstention without a safe verdict", async () => {
  vi.mocked(api.predict).mockResolvedValue({
    ...response,
    class_id: null,
    uncertain: true,
    predicted_category: "Uncertain — Manual Review Recommended",
    uncertainty_reasons: ["Confidence too low."],
  });
  setup();
  fireEvent.click(screen.getByText("Load example"));
  fireEvent.click(screen.getByRole("button", { name: /Analyze code/ }));
  expect(
    await screen.findByText("Uncertain — Manual Review Recommended"),
  ).toBeInTheDocument();
  expect(screen.getByText("Confidence too low.")).toBeInTheDocument();
});
