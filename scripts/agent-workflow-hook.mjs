// Agent lifecycle hook guard for docs-driven projects.
// It nudges agents to run the documented workflow and blocks high-risk deletion
// paths, but it never updates docs or archives files by itself.

const HOOK_EVENT_NAMES = new Set(["SessionStart", "Stop", "PreToolUse"]);

const SESSION_CONTEXT = [
  "Docs-driven workflow reminder:",
  "- Read AGENTS.md, TODO.md, _docs/documentation_guide.md, and relevant _docs/standards before implementation.",
  "- Skills are not automatic. Use implementation-prep before multi-file or document-aligned work.",
  "- Use docs-inventory for current-state triage, handoff discovery, stale-doc audits, or concerns that docs have become ceremonial.",
  "- For Size >= M or Risk >= Medium tasks, use docs-prep and qa-prep before implementation, and qa-review before completion.",
  "- Use docs-cleanup when draft/plan/survey/archive boundaries or substantial documentation cleanup are involved.",
  "- Hooks are guardrails only: do not let them replace judgement, QA evidence, or explicit verification notes.",
].join("\n");

const CLOSURE_TERMS_RE =
  /check-docs|validate-|docs-inventory|qa-review|docs-cleanup|post-implementation|verification|verdict|residual risk|未検証|検証|残リスク|実行できなかった|deferred/i;

const COMPLETION_TERMS_RE =
  /完了|対応しました|実装しました|更新しました|修正しました|追加しました|done|completed|implemented|fixed|updated|added|finished|pass/i;

const QUESTION_AT_END_RE = /[?？]\s*$/;

const normalizePath = (path) => {
  const segments = [];
  for (const segment of String(path ?? "").replaceAll("\\", "/").split("/")) {
    if (segment === "" || segment === ".") continue;
    if (segment === "..") segments.pop();
    else segments.push(segment);
  }
  return segments.join("/");
};

const unique = (items) => [...new Set(items.filter(Boolean))];

export const parsePorcelainPaths = (statusOutput) => {
  const paths = [];
  for (const rawLine of String(statusOutput ?? "").split(/\r?\n/)) {
    const line = rawLine.trimEnd();
    if (line === "") continue;
    const body = line.slice(3).trim();
    if (body.includes(" -> ")) {
      const [from, to] = body.split(" -> ").map((value) =>
        value.replace(/^"|"$/g, "")
      );
      paths.push(normalizePath(from), normalizePath(to));
    } else {
      paths.push(normalizePath(body.replace(/^"|"$/g, "")));
    }
  }
  return unique(paths);
};

const pathFromToolInput = (toolInput) => {
  if (!toolInput || typeof toolInput !== "object") return "";
  return normalizePath(
    toolInput.file_path ?? toolInput.path ?? toolInput.target_file ?? "",
  );
};

const commandFromToolInput = (toolInput) => {
  if (!toolInput || typeof toolInput !== "object") return "";
  return String(toolInput.command ?? toolInput.cmd ?? "");
};

const includesSensitivePath = (value) =>
  /(^|[\/\s'"`])(\.env(\.|$|[\/\s'"`])|id_rsa\b|id_ed25519\b|\.pem\b|\.key\b)/i
    .test(String(value ?? ""));

const protectedArchiveMove = (command) =>
  /\b(git\s+)?mv\b[\s\S]*_docs\/(intent|qa|guide|reference)\b[\s\S]*_docs\/archives\b/i
    .test(command) ||
  /\b(git\s+)?mv\b[\s\S]*_docs\/archives\/(intent|qa|guide|reference)\b/i
    .test(command);

const destructiveCommandReason = (command) => {
  const text = String(command ?? "");
  const checks = [
    {
      re: /(^|[;&|()\s])git\s+rm(\s|$)/,
      reason:
        "git rm is blocked by this template. Propose permanent deletion to the user, or use archive movement only after the checklist passes.",
    },
    {
      re: /(^|[;&|()\s])rm\s+(-[^\s]+\s+)?/,
      reason:
        "rm is blocked by this template. Propose permanent deletion to the user, or use archive movement only after the checklist passes.",
    },
    {
      re: /(^|[;&|()\s])git\s+reset\s+--hard(\s|$)/,
      reason:
        "git reset --hard is blocked because it can discard user or agent work.",
    },
    {
      re: /(^|[;&|()\s])git\s+clean(\s|$)/,
      reason: "git clean is blocked because it can permanently remove files.",
    },
    {
      re: /(^|[;&|()\s])git\s+checkout\s+--(\s|$)/,
      reason:
        "git checkout -- is blocked because it can discard local changes.",
    },
  ];
  for (const check of checks) {
    if (check.re.test(text)) return check.reason;
  }
  if (protectedArchiveMove(text)) {
    return "Do not move intent, QA, guide, or reference docs into archives. Only draft, plan, and survey docs can be archived after the checklist passes.";
  }
  if (
    includesSensitivePath(text) &&
    /\b(cat|less|more|sed|awk|rg|grep|python|node|deno|cp|mv)\b/.test(text)
  ) {
    return "This command appears to touch sensitive credential-like files. Avoid reading or copying .env, key, or token material.";
  }
  return null;
};

const patchDeletionReason = (command) => {
  if (!/\*\*\* Delete File:/.test(command)) return null;
  return "File deletion through apply_patch is blocked by this template. Propose permanent deletion to the user, or use archive movement only after the checklist passes.";
};

export const analyzePreToolUse = (input) => {
  const toolName = String(input?.tool_name ?? input?.toolName ?? "");
  const toolInput = input?.tool_input ?? input?.toolInput ?? {};
  const command = commandFromToolInput(toolInput);
  const filePath = pathFromToolInput(toolInput);

  if (/bash|shell/i.test(toolName)) {
    const reason = destructiveCommandReason(command);
    if (reason) return { decision: "block", reason };
  }

  if (/apply_patch|edit|write|multiedit/i.test(toolName)) {
    const reason = patchDeletionReason(command);
    if (reason) return { decision: "block", reason };
    if (includesSensitivePath(filePath)) {
      return {
        decision: "block",
        reason:
          "Edits to sensitive credential-like files are blocked. Use .env.example or a documented non-secret placeholder instead.",
      };
    }
  }

  return null;
};

const relevantStopPaths = (paths) => {
  const normalized = unique(paths.map(normalizePath));
  return {
    all: normalized,
    todo: normalized.filter((path) => path === "TODO.md"),
    docs: normalized.filter((path) =>
      path.startsWith("_docs/") || [
        "README.md",
        "QUICKSTART.md",
        "AGENTS.md",
        "CLAUDE.md",
      ].includes(path)
    ),
    workflow: normalized.filter((path) =>
      path === "AGENTS.md" ||
      path === "CLAUDE.md" ||
      path.startsWith(".codex/") ||
      path === ".claude/settings.json" ||
      path.startsWith(".agents/skills/") ||
      path.startsWith(".claude/skills/") ||
      path.startsWith(".github/workflows/") ||
      path.startsWith("_docs/standards/") ||
      path.startsWith("scripts/validate-") ||
      path === "scripts/check-docs.sh" ||
      path === "scripts/scope.mjs" ||
      path === "scripts/agent-workflow-hook.mjs" ||
      path === "scripts/test-agent-workflow-smoke.mjs"
    ),
    archive: normalized.filter((path) => path.startsWith("_docs/archives/")),
    temporaryDocs: normalized.filter((path) =>
      /^_docs\/(draft|plan|survey)\//.test(path)
    ),
    qaDocs: normalized.filter((path) => path.startsWith("_docs/qa/")),
  };
};

const looksLikeCompletion = (message) => {
  const text = String(message ?? "").trim();
  if (text === "") return true;
  if (QUESTION_AT_END_RE.test(text) && !COMPLETION_TERMS_RE.test(text)) {
    return false;
  }
  return COMPLETION_TERMS_RE.test(text);
};

const hasClosureEvidence = (message) => CLOSURE_TERMS_RE.test(message ?? "");

const listSome = (label, paths) => {
  if (paths.length === 0) return null;
  const shown = paths.slice(0, 5).map((path) => `  - ${path}`).join("\n");
  const suffix = paths.length > 5
    ? `\n  - ...and ${paths.length - 5} more`
    : "";
  return `${label}:\n${shown}${suffix}`;
};

export const analyzeStop = ({ input = {}, dirtyPaths = [] }) => {
  if (input.stop_hook_active === true) return null;

  const grouped = relevantStopPaths(dirtyPaths);
  const hasRelevantChange = grouped.todo.length > 0 ||
    grouped.docs.length > 0 ||
    grouped.workflow.length > 0;
  if (!hasRelevantChange) return null;

  const lastMessage = String(
    input.last_assistant_message ?? input.lastAssistantMessage ?? "",
  );
  if (!looksLikeCompletion(lastMessage)) return null;
  if (hasClosureEvidence(lastMessage)) return null;

  const sections = [
    listSome("Changed workflow-sensitive files", grouped.workflow),
    listSome("Changed documentation files", grouped.docs),
    listSome("Changed TODO files", grouped.todo),
  ].filter(Boolean).join("\n\n");

  const actions = [
    "Before finishing, handle the docs-driven closure explicitly:",
    "- If TODO.md or _docs changed, run ./scripts/check-docs.sh or state why it cannot run.",
    "- If the request is current-state triage, handoff discovery, or documentation health review, use docs-inventory before cleanup.",
    "- If the task is Size >= M or Risk >= Medium, use qa-review and record verification before completion.",
    "- If draft/plan/survey cleanup or archives are involved, use docs-cleanup. Do not archive intent or QA docs.",
    "- Mention commands actually run and remaining gaps in the final response.",
  ].join("\n");

  return {
    decision: "block",
    reason: `${sections}\n\n${actions}`,
  };
};

const readStdin = async () => {
  const chunks = [];
  const buffer = new Uint8Array(8192);
  while (true) {
    const n = await Deno.stdin.read(buffer);
    if (n === null) break;
    chunks.push(buffer.slice(0, n));
  }
  const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const merged = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  return new TextDecoder().decode(merged);
};

const parseHookInput = (raw) => {
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
};

const runGitStatus = async () => {
  const command = new Deno.Command("git", {
    args: ["status", "--short"],
    stdout: "piped",
    stderr: "piped",
  });
  const output = await command.output();
  if (!output.success) return [];
  return parsePorcelainPaths(new TextDecoder().decode(output.stdout));
};

const jsonOut = (value) => {
  console.log(JSON.stringify(value));
};

const blockOut = (eventName, reason) => {
  if (eventName === "PreToolUse") {
    jsonOut({
      decision: "block",
      reason,
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    });
    return;
  }
  jsonOut({ decision: "block", reason });
};

const sessionStartOut = () => {
  jsonOut({
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: SESSION_CONTEXT,
    },
  });
};

const inferEventName = (arg, input) => {
  const fromInput = input.hook_event_name ?? input.hookEventName;
  if (HOOK_EVENT_NAMES.has(fromInput)) return fromInput;
  if (arg === "session-start") return "SessionStart";
  if (arg === "stop") return "Stop";
  if (arg === "pre-tool-use") return "PreToolUse";
  return fromInput ?? arg ?? "";
};

const main = async () => {
  const raw = await readStdin();
  const input = parseHookInput(raw);
  const eventName = inferEventName(Deno.args[0], input);

  if (eventName === "SessionStart") {
    sessionStartOut();
    return;
  }

  if (eventName === "PreToolUse") {
    const result = analyzePreToolUse(input);
    if (result?.decision === "block") blockOut("PreToolUse", result.reason);
    return;
  }

  if (eventName === "Stop") {
    const dirtyPaths = await runGitStatus();
    const result = analyzeStop({ input, dirtyPaths });
    if (result?.decision === "block") blockOut("Stop", result.reason);
  }
};

if (import.meta.main) {
  main().catch((err) => {
    console.error(`agent-workflow-hook failed: ${err.message}`);
    Deno.exit(1);
  });
}
