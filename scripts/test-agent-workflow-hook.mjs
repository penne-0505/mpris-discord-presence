import {
  analyzePreToolUse,
  analyzeStop,
  analyzeUserPromptSubmit,
  auditEvidenceCount,
  parsePorcelainPaths,
} from "./agent-workflow-hook.mjs";

const assert = (condition, message) => {
  if (!condition) {
    console.error(`FAIL ${message}`);
    Deno.exit(1);
  }
  console.log(`PASS ${message}`);
};

assert(
  parsePorcelainPaths(" M TODO.md\nR  old.md -> new.md\n?? scripts/x.mjs\n")
    .join(",") === "TODO.md,old.md,new.md,scripts/x.mjs",
  "parse git porcelain paths",
);

assert(
  analyzeUserPromptSubmit().context.includes("plausible counterevidence") &&
    analyzeUserPromptSubmit().context.includes("Scope") &&
    analyzeUserPromptSubmit().context.length < 240,
  "AC-001 INV-001 keep per-prompt audit short and evidence-based",
);

assert(
  analyzePreToolUse({
    tool_name: "apply_patch",
    tool_input: { command: "*** Begin Patch\n*** Update File: README.md\n" },
  })?.context.includes("root cause") &&
    analyzePreToolUse({
      tool_name: "Write",
      tool_input: { file_path: "src/example.ts" },
    })?.context.includes("silently expanding scope"),
  "AC-002 INV-002 add durable write audit context",
);

assert(
  analyzePreToolUse({
    tool_name: "Read",
    tool_input: { file_path: "README.md" },
  }) === null,
  "INV-002 avoid write audit noise on read-only tools",
);

assert(
  analyzePreToolUse({
    tool_name: "Bash",
    tool_input: { command: "git rm _docs/qa/Core/x/test-plan.md" },
  })?.decision === "block",
  "block git rm",
);

assert(
  analyzePreToolUse({
    tool_name: "Bash",
    tool_input: { command: "rm -rf _docs/intent/Core/x" },
  })?.decision === "block",
  "block rm",
);

assert(
  analyzePreToolUse({
    tool_name: "apply_patch",
    tool_input: { command: "*** Begin Patch\n*** Delete File: README.md\n" },
  })?.decision === "block",
  "block apply_patch file deletion",
);

assert(
  analyzePreToolUse({
    tool_name: "Write",
    tool_input: { file_path: ".env" },
  })?.decision === "block",
  "block sensitive file edit",
);

assert(
  analyzeStop({
    dirtyPaths: ["TODO.md", ".codex/hooks.json"],
    input: { last_assistant_message: "対応しました。" },
  })?.decision === "block",
  "stop hook nudges missing closure evidence",
);

assert(
  analyzeStop({
    dirtyPaths: ["TODO.md"],
    input: {
      last_assistant_message: "対応しました。qa-reviewと検証はPASSです。",
    },
  })?.decision === "block",
  "AC-003 INV-003 stop hook rejects verification without independent audit",
);

assert(
  analyzeStop({
    dirtyPaths: ["TODO.md"],
    input: {
      last_assistant_message:
        "対応しました。qa-reviewと検証はPASSです。反証候補を確認し、影響範囲と長期保守性を再監査しました。残リスクはありません。",
    },
  }) === null,
  "AC-003 INV-003 stop hook allows verification with multi-perspective audit",
);

assert(
  auditEvidenceCount("反証を確認し、影響範囲と長期保守性を監査した。") === 3,
  "INV-003 count distinct audit perspectives",
);

assert(
  analyzeStop({
    dirtyPaths: ["README.md"],
    input: {
      stop_hook_active: true,
      last_assistant_message: "対応しました。",
    },
  }) === null,
  "stop hook avoids recursive block",
);
