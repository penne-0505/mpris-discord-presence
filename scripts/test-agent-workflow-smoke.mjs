// Lightweight smoke checks for agent workflow activation surfaces.

const read = (path) => Deno.readTextFile(path);

const assert = (condition, message) => {
  if (!condition) {
    console.error(`FAIL ${message}`);
    Deno.exit(1);
  }
  console.log(`PASS ${message}`);
};

const json = async (path) => JSON.parse(await read(path));

const contains = (text, ...needles) =>
  needles.every((needle) => text.includes(needle));

const codexHooks = await json(".codex/hooks.json");
const claudeSettings = await json(".claude/settings.json");
const agentHook = await read("scripts/agent-workflow-hook.mjs");
const agentsInventory = await read(".agents/skills/docs-inventory/SKILL.md");
const claudeInventory = await read(".claude/skills/docs-inventory/SKILL.md");
const agentsCleanup = await read(".agents/skills/docs-cleanup/SKILL.md");
const claudeCleanup = await read(".claude/skills/docs-cleanup/SKILL.md");
const agentsGuide = await read("AGENTS.md");

const hookEvents = (config) => Object.keys(config.hooks ?? {});

assert(
  ["SessionStart", "PreToolUse", "Stop"].every((event) =>
    hookEvents(codexHooks).includes(event)
  ),
  "Codex hooks include SessionStart, PreToolUse, and Stop",
);

assert(
  ["SessionStart", "PreToolUse", "Stop"].every((event) =>
    hookEvents(claudeSettings).includes(event)
  ),
  "Claude hooks include SessionStart, PreToolUse, and Stop",
);

assert(
  JSON.stringify(codexHooks).includes("scripts/agent-workflow-hook.mjs") &&
    JSON.stringify(claudeSettings).includes("scripts/agent-workflow-hook.mjs"),
  "hook configs call the shared workflow hook script",
);

assert(
  contains(agentHook, "docs-inventory", "docs-cleanup", "qa-review"),
  "workflow hook reminds agents about inventory, cleanup, and QA review",
);

assert(
  agentsInventory === claudeInventory,
  "docs-inventory skill is synced across .agents and .claude",
);

assert(
  agentsCleanup === claudeCleanup,
  "docs-cleanup skill is synced across .agents and .claude",
);

assert(
  contains(agentsInventory, "read-only", "stale documentation audit"),
  "docs-inventory remains a read-only stale-doc audit entrypoint",
);

assert(
  contains(agentsCleanup, "Archive Checklist", "Do not archive"),
  "docs-cleanup keeps archive boundary guidance",
);

assert(
  contains(agentsGuide, "docs-inventory", "qa-review"),
  "AGENTS.md exposes inventory and QA review entrypoints",
);
