import Editor from "@monaco-editor/react";

export function CodeEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        height: "100%",
      }}
    >
      <Editor
        height="100%"
        defaultLanguage="python"
        value={value}
        onChange={(v) => onChange(v ?? "")}
        theme="vs"
        options={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 13.5,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          padding: { top: 14 },
          lineNumbersMinChars: 3,
        }}
      />
    </div>
  );
}
