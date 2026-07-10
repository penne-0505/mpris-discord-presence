import {
  analyzePreToolUse,
  analyzeStop,
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
      last_assistant_message:
        "対応しました。docs-inventoryで棚卸しし、検証として ./scripts/check-docs.sh を実行しました。",
    },
  }) === null,
  "stop hook allows explicit closure evidence",
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
