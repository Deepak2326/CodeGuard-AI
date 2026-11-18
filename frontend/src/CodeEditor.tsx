import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api.js";
import "monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution.js";
import "monaco-editor/esm/vs/basic-languages/java/java.contribution.js";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
// Bundle locally: no CDN and no transmission of source to an editor service.
self.MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });
export default function CodeEditor({
  code,
  language,
  onChange,
  disabled,
}: {
  code: string;
  language: string;
  onChange: (code: string) => void;
  disabled: boolean;
}) {
  return (
    <Editor
      height="420px"
      language={language === "c" ? "cpp" : language}
      theme="vs-dark"
      value={code}
      onChange={(value) => onChange(value || "")}
      loading={<p className="muted">Loading editor…</p>}
      options={{
        readOnly: disabled,
        minimap: { enabled: false },
        fontSize: 14,
        lineHeight: 24,
        padding: { top: 20 },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        wordWrap: "on",
        ariaLabel: "Source code editor",
      }}
    />
  );
}
