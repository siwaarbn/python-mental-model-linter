import { useState } from "react";
import type { FeedbackCard } from "../types";

/**
 * Plain-language headings, chosen with the supervisor's feedback in mind:
 * no "Layer 1/2/3/4" model framing, no rule IDs, no confidence/severity
 * jargon on screen. The underlying four-layer structure (Narciss /
 * Sorva) is still exactly what drives the sequence -- it's just not
 * exposed as a numbered technical model anymore.
 */
const LAYER_HEADINGS = [
  "What happened",
  "Why this happens in Python",
  "A different way to think about it",
  "Think it through",
];

function layerText(card: FeedbackCard, index: number): string {
  switch (index) {
    case 0: return card.layer1_observation;
    case 1: return card.layer2_conceptual_explanation;
    case 2: return card.layer3_mental_model_correction;
    case 3: return card.layer4_reflection_prompt;
    default: return "";
  }
}

/** Extracts the exact source line the finding points to, so the student sees
 * their own code as a concrete example instead of only a prose description. */
function flaggedLine(sourceCode: string, lineNumber: number | null): string | null {
  if (lineNumber == null) return null;
  const lines = sourceCode.split("\n");
  const line = lines[lineNumber - 1];
  return line != null ? line.trim() : null;
}

function CaseNote({ card, sourceCode }: { card: FeedbackCard; sourceCode: string }) {
  const [openUpTo, setOpenUpTo] = useState(0);
  const example = flaggedLine(sourceCode, card.line);

  return (
    <div style={{ borderBottom: "1px solid var(--border)", padding: "22px 0" }}>
      <div style={{ fontFamily: "var(--font-voice)", fontSize: 19, fontWeight: 600, color: "var(--text-primary)", marginBottom: 14 }}>
        {card.misconception_name}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {LAYER_HEADINGS.map((heading, i) => {
          const revealed = i <= openUpTo;
          const isNext = i === openUpTo + 1;
          const isReflection = i === 3;

          return (
            <div key={heading} style={{ opacity: revealed ? 1 : isNext ? 0.6 : 0.25 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: revealed ? 6 : 0 }}>
                {heading}
              </div>

              {revealed && i === 0 && example && (
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 13,
                    background: "var(--bg-sunken)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    padding: "8px 12px",
                    marginBottom: 8,
                    color: "var(--text-primary)",
                  }}
                >
                  {example}
                </div>
              )}

              {revealed ? (
                <div
                  style={{
                    fontSize: 14,
                    lineHeight: 1.55,
                    color: "var(--text-primary)",
                    fontStyle: "normal",
                    fontFamily: "var(--font-sans)",
                    fontWeight: 400,
                  }}
                >
                  {layerText(card, i)}
                </div>
              ) : isNext ? (
                <button style={{ fontSize: 12, padding: "4px 10px" }} onClick={() => setOpenUpTo(i)}>
                  Show me &rarr;
                </button>
              ) : null}

              {revealed && isReflection && example && (
                <div
                  style={{
                    marginTop: 10,
                    background: "var(--bg-sunken)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    padding: "10px 12px",
                  }}
                >
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>
                    Your code, for reference
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--text-primary)" }}>
                    {example}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function FeedbackPanel({
  findings,
  parseError,
  loading,
  hasRun,
  sourceCode,
  exampleTests,
}: {
  findings: FeedbackCard[];
  parseError: string | null;
  loading: boolean;
  hasRun: boolean;
  sourceCode: string;
  exampleTests: string;
}) {
  return (
    <div
      style={{
        background: "var(--bg-panel)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "18px 20px",
        height: "100%",
        overflowY: "auto",
      }}
    >
      <div style={{ fontFamily: "var(--font-voice)", fontSize: 18, marginBottom: 2 }}>Feedback</div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
        {loading
          ? "Analyzing\u2026"
          : parseError
          ? "Could not run your code"
          : findings.length === 0 && hasRun
          ? "No misconceptions detected"
          : findings.length === 0
          ? "Run your code to see feedback"
          : `${findings.length} thing${findings.length === 1 ? "" : "s"} to look at`}
      </div>

      {loading && <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Running detection rules&hellip;</div>}

      {!loading && parseError && (
        <div
          style={{
            background: "var(--amber-soft)",
            border: "1px solid var(--amber)",
            borderRadius: "var(--radius-sm)",
            padding: "12px 14px",
            fontSize: 13,
            color: "var(--text-primary)",
            fontFamily: "var(--font-mono)",
            whiteSpace: "pre-wrap",
          }}
        >
          {parseError}
        </div>
      )}

      {!loading && !parseError && findings.length === 0 && hasRun && (
        <div>
          <div
            style={{
              background: "var(--accent-soft)",
              border: "1px solid var(--accent)",
              borderRadius: "var(--radius-sm)",
              padding: "12px 14px",
              fontSize: 13.5,
              color: "var(--text-primary)",
              marginBottom: 16,
            }}
          >
            Nice work — none of the known misconception patterns showed up in this
            submission. That's a good sign, though it doesn't guarantee everything is
            correct. Try the test cases below to double-check your solution.
          </div>

          {exampleTests && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 8 }}>
                Try these test cases
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {exampleTests.split("\n").map((line, i) => (
                  <div
                    key={i}
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 13,
                      background: "var(--bg-sunken)",
                      borderRadius: "var(--radius-sm)",
                      padding: "8px 12px",
                      color: "var(--text-primary)",
                    }}
                  >
                    {line}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!loading &&
        !parseError &&
        findings.map((card, i) => <CaseNote key={`${card.rule_id}-${i}`} card={card} sourceCode={sourceCode} />)}
    </div>
  );
}