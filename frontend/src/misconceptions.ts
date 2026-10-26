/**
 * Single source of truth for misconception display labels + colors.
 * Used by Home (category filter + task cards), StudentWorkspace (feedback
 * accents), and InstructorDashboard (charts, roster, Hinweise) so the same
 * M-code always reads as the same color everywhere in the app.
 */
export interface MisconceptionMeta {
  label: string;
  color: string; // vivid accent, used for text/borders
  soft: string; // light tint of the same hue, used for backgrounds/chips
}

export const MISCONCEPTION_META: Record<string, MisconceptionMeta> = {
  M1: { label: "Variable Persistence", color: "#e0457b", soft: "#fdeaf1" },
  M2: { label: "Assignment Direction", color: "#7c5cf0", soft: "#f1edfd" },
  M3: { label: "Identity vs Equality", color: "#1f9e77", soft: "#e6f6f0" },
  M4: { label: "Loop Termination", color: "#e08a1f", soft: "#fdf1de" },
  M5: { label: "Return Semantics", color: "#2f8fd6", soft: "#e8f3fc" },
  M6: { label: "Scope", color: "#d6336c", soft: "#fbe6ee" },
  M7: { label: "Accumulation Pattern", color: "#0ca678", soft: "#e3f7f0" },
  M8: { label: "Mutation vs Return Value", color: "#f08c00", soft: "#fef1e0" },
  M9: { label: "Method Reference vs Call", color: "#5c7cfa", soft: "#ecf0fe" },
  M10: { label: "Operator Precedence", color: "#ae3ec9", soft: "#f6e9fa" },
  M11: { label: "Truthiness", color: "#12a3a3", soft: "#e3f6f6" },
};

export function misconceptionLabel(id: string): string {
  return MISCONCEPTION_META[id]?.label ?? id;
}

export function misconceptionColor(id: string): string {
  return MISCONCEPTION_META[id]?.color ?? "#6b7280";
}

export function misconceptionSoft(id: string): string {
  return MISCONCEPTION_META[id]?.soft ?? "#f1f2f4";
}

/** All misconception ids in M1..M11 order, for building filter chips. */
export const ALL_MISCONCEPTION_IDS = Object.keys(MISCONCEPTION_META);
