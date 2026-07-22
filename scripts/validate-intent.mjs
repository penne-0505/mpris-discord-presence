// Deno版 intent schema validator: schema v2 の why-first decision record を検証する

import { loadScope, makeInScope } from "./scope.mjs";

const INTENT_SCHEMA = 2;
const INTENT_PATH_RE =
  /^_docs\/intent\/([A-Za-z][A-Za-z0-9-]*)\/([a-z0-9]+(?:-[a-z0-9]+)*)\/decision\.md$/;

const normalizePath = (path) => path.replaceAll("\\", "/");

const walkFiles = async function* (dir) {
  try {
    for await (const entry of Deno.readDir(dir)) {
      const path = `${dir}/${entry.name}`;
      if (entry.isDirectory) {
        yield* walkFiles(path);
      } else if (entry.isFile && entry.name.endsWith(".md")) {
        yield normalizePath(path);
      }
    }
  } catch (err) {
    if (!(err instanceof Deno.errors.NotFound)) throw err;
  }
};

const fileOrDir = async (path) => {
  const stat = await Deno.stat(path);
  return stat.isFile ? "file" : "dir";
};

const stripInlineComment = (value) => {
  let quote = null;
  for (let i = 0; i < value.length; i += 1) {
    const ch = value[i];
    if ((ch === '"' || ch === "'") && value[i - 1] !== "\\") {
      quote = quote === ch ? null : quote ?? ch;
    }
    if (ch === "#" && quote === null) return value.slice(0, i).trim();
  }
  return value.trim();
};

const parseScalar = (raw) => {
  const value = stripInlineComment(raw);
  if (/^-?\d+$/.test(value)) return Number(value);
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
};

const parseFrontMatter = (src) => {
  const lines = src.split(/\r?\n/);
  if (lines[0] !== "---") return { attrs: null, error: "missing front matter" };
  const end = lines.findIndex((line, index) => index > 0 && line === "---");
  if (end === -1) return { attrs: null, error: "front matter is not closed" };

  const attrs = {};
  for (let i = 1; i < end; i += 1) {
    const match = lines[i].match(/^([A-Za-z0-9_]+):(?:\s*(.*))?$/);
    if (!match) continue;
    const [, key, rest = ""] = match;
    attrs[key] = parseScalar(rest);
  }
  return { attrs, error: null };
};

const stripCodeBlocks = (src) => {
  const output = [];
  let inFence = false;
  for (const line of src.split(/\r?\n/)) {
    if (/^\s*```/.test(line)) {
      inFence = !inFence;
      output.push("");
      continue;
    }
    output.push(inFence ? "" : line);
  }
  return output.join("\n");
};

const sectionContent = (src, heading) => {
  const lines = stripCodeBlocks(src).split(/\r?\n/);
  const start = lines.findIndex((line) => line.trim() === `## ${heading}`);
  if (start === -1) return null;
  const end = lines.findIndex((line, index) =>
    index > start && /^##\s+/.test(line)
  );
  return lines.slice(start + 1, end === -1 ? lines.length : end).join("\n");
};

const decisionEntries = (content) => {
  const lines = content.split(/\r?\n/);
  const entries = [];
  for (let i = 0; i < lines.length; i += 1) {
    const match = lines[i].match(/^###\s+(DEC-\d{3}):\s+(.+)$/);
    if (!match) continue;
    const end = lines.findIndex((line, index) =>
      index > i && /^###\s+DEC-\d{3}:/.test(line)
    );
    entries.push({
      id: match[1],
      title: match[2].trim(),
      body: lines.slice(i + 1, end === -1 ? lines.length : end).join("\n"),
    });
    if (end !== -1) i = end - 1;
  }
  return entries;
};

const fieldValue = (body, name) =>
  body.match(new RegExp(`^- \\*\\*${name}\\*\\*:\\s*(.+)$`, "m"))?.[1]
    ?.trim();

const isNoneLike = (content) => {
  const withoutComments = content.replace(/<!--[\s\S]*?-->/g, "").trim();
  return /^(None|N\/A|なし)$/i.test(withoutComments);
};

const add = (items, file, message) => items.push({ file, message });

const validateV2 = (file, src, errors) => {
  const requiredHeadings = [
    "Context",
    "Decisions",
    "Consequences / Impact",
    "Quality Implications",
    "Intent-derived Invariants",
    "Rollback / Follow-ups",
  ];
  for (const heading of requiredHeadings) {
    if (sectionContent(src, heading) === null) {
      add(errors, file, `intent_schema 2 missing heading: ${heading}`);
    }
  }

  const decisions = decisionEntries(sectionContent(src, "Decisions") ?? "");
  if (decisions.length === 0) {
    add(errors, file, "intent_schema 2 requires at least one DEC-001 entry");
  }

  const decisionIds = new Set();
  for (const decision of decisions) {
    if (decisionIds.has(decision.id)) {
      add(errors, file, `duplicate decision ID: ${decision.id}`);
    }
    decisionIds.add(decision.id);
    for (const field of ["What", "Why", "Change freedom"]) {
      if (!fieldValue(decision.body, field)) {
        add(errors, file, `${decision.id} missing substantive ${field}`);
      }
    }
    for (const field of ["Why not", "Revisit when"]) {
      const fieldLine = new RegExp(`^- \\*\\*${field}\\*\\*:`, "m");
      if (fieldLine.test(decision.body) && !fieldValue(decision.body, field)) {
        add(errors, file, `${decision.id} has empty optional field: ${field}`);
      }
    }
  }

  const invariants = sectionContent(src, "Intent-derived Invariants") ?? "";
  if (isNoneLike(invariants)) return;

  const invariantLines = invariants
    .replace(/<!--[\s\S]*?-->/g, "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /^- INV-/.test(line));
  if (invariantLines.length === 0) {
    add(
      errors,
      file,
      "Intent-derived Invariants must be None or use INV-001 (from DEC-001)",
    );
    return;
  }

  const invariantIds = new Set();
  for (const line of invariantLines) {
    const match = line.match(
      /^- (INV-\d{3}) \(from (DEC-\d{3})\):\s*(.+)$/,
    );
    if (!match) {
      add(
        errors,
        file,
        `invalid invariant format: ${line}`,
      );
      continue;
    }
    const [, invariantId, decisionId] = match;
    if (invariantIds.has(invariantId)) {
      add(errors, file, `duplicate invariant ID: ${invariantId}`);
    }
    invariantIds.add(invariantId);
    if (!decisionIds.has(decisionId)) {
      add(
        errors,
        file,
        `${invariantId} references missing decision ${decisionId}`,
      );
    }
  }
};

const collectFiles = async (target) => {
  if (await fileOrDir(target) === "file") return [normalizePath(target)];
  const files = [];
  for await (const file of walkFiles(target)) files.push(file);
  return files;
};

const run = async () => {
  const fixtureIndex = Deno.args.indexOf("--fixture");
  const fixtureTarget = fixtureIndex === -1
    ? null
    : Deno.args[fixtureIndex + 1];
  if (fixtureIndex !== -1 && !fixtureTarget) {
    console.error("ERROR: --fixture requires a file or directory");
    Deno.exit(1);
  }

  const target = fixtureTarget ??
    Deno.args.find((arg) => !arg.startsWith("-")) ??
    "_docs/intent";
  const inScope = makeInScope(await loadScope());
  const errors = [];

  for (const file of await collectFiles(target)) {
    if (!fixtureTarget && !inScope(file)) continue;
    const src = await Deno.readTextFile(file);
    const { attrs, error } = parseFrontMatter(src);
    if (error) {
      add(errors, file, error);
      continue;
    }

    const logicalPath = typeof attrs.fixture_path === "string"
      ? attrs.fixture_path
      : file;
    if (!INTENT_PATH_RE.test(logicalPath)) {
      add(errors, file, `invalid canonical intent path: ${logicalPath}`);
      continue;
    }

    if (!("intent_schema" in attrs)) continue;
    if (attrs.intent_schema !== INTENT_SCHEMA) {
      add(
        errors,
        file,
        `intent_schema must be ${INTENT_SCHEMA} when present`,
      );
      continue;
    }
    validateV2(file, src, errors);
  }

  if (errors.length > 0) {
    for (const { file, message } of errors) {
      console.error(`ERROR: ${file}\n  - ${message}`);
    }
    Deno.exit(1);
  }
};

await run();
