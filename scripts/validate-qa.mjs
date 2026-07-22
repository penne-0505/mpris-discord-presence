// Deno版 QA document validator: npm / remote import 依存なし

import { loadScope, makeInScope } from "./scope.mjs";

const TODO_FILE = "TODO.md";
const QA_SCHEMA = 2;
const RISKS = ["Low", "Medium", "High", "Critical"];
const QA_STATUS_VALUES = [
  "planned",
  "in-progress",
  "verified",
  "partial",
  "failed",
  "blocked",
];
const TEST_MATRIX_STATUS_VALUES = [
  "planned",
  "covered",
  "verified",
  "deferred",
  "not-applicable",
];
const VERDICTS = ["PASS", "PARTIAL", "FAIL", "BLOCKED"];
const VERDICT_STATUS = {
  PASS: "verified",
  PARTIAL: "partial",
  FAIL: "failed",
  BLOCKED: "blocked",
};
const QA_PATH_RE =
  /^_docs\/qa\/([A-Za-z][A-Za-z0-9-]*)\/([a-z0-9]+(?:-[a-z0-9]+)*)\/(test-plan|verification)\.md$/;
const TODO_FIELD_RE = /^- \*\*([A-Za-z][A-Za-z ]*)\*\*:\s*(.*)$/;

const normalizePath = (path) => {
  const segments = [];
  for (const segment of path.replaceAll("\\", "/").split("/")) {
    if (segment === "" || segment === ".") continue;
    if (segment === "..") segments.pop();
    else segments.push(segment);
  }
  return segments.join("/");
};

const walkFiles = async function* (dir, predicate = () => true) {
  try {
    for await (const entry of Deno.readDir(dir)) {
      const path = `${dir}/${entry.name}`;
      if (entry.isDirectory) {
        yield* walkFiles(path, predicate);
      } else if (entry.isFile && predicate(path)) {
        yield normalizePath(path);
      }
    }
  } catch (err) {
    if (!(err instanceof Deno.errors.NotFound)) throw err;
  }
};

const exists = async (path) => {
  try {
    const stat = await Deno.stat(path);
    return stat.isFile;
  } catch (err) {
    if (err instanceof Deno.errors.NotFound) return false;
    throw err;
  }
};

const fileOrDir = async (path) => {
  const stat = await Deno.stat(path);
  return stat.isFile ? "file" : "dir";
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

const splitInlineArray = (value) => {
  const items = [];
  let current = "";
  let quote = null;
  for (const ch of value) {
    if ((ch === '"' || ch === "'") && current.at(-1) !== "\\") {
      quote = quote === ch ? null : quote ?? ch;
    }
    if (ch === "," && quote === null) {
      items.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }
  if (current.trim() !== "") items.push(current.trim());
  return items;
};

const parseScalar = (raw) => {
  const value = stripInlineComment(raw);
  if (value === "") return "";
  if (value === "[]") return [];
  if (value.startsWith("[") && value.endsWith("]")) {
    const inner = value.slice(1, -1).trim();
    if (inner === "") return [];
    return splitInlineArray(inner).map(parseScalar);
  }
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  if (/^-?\d+$/.test(value)) return Number(value);
  return value;
};

const parseFrontMatter = (src) => {
  const lines = src.split(/\r?\n/);
  if (lines[0] !== "---") return { attrs: null, error: "missing front matter" };
  const end = lines.findIndex((line, index) => index > 0 && line === "---");
  if (end === -1) return { attrs: null, error: "front matter is not closed" };

  const attrs = {};
  for (let i = 1; i < end; i += 1) {
    const line = lines[i];
    if (line.trim() === "" || line.trimStart().startsWith("#")) continue;
    const match = line.match(/^([A-Za-z0-9_]+):(?:\s*(.*))?$/);
    if (!match) {
      return { attrs: null, error: `unsupported front matter line: ${line}` };
    }
    const [, key, rest = ""] = match;
    if (rest.trim() !== "") {
      attrs[key] = parseScalar(rest);
      continue;
    }
    const values = [];
    let cursor = i + 1;
    while (cursor < end) {
      const item = lines[cursor].match(/^\s+-\s+(.*)$/);
      if (!item) break;
      values.push(parseScalar(item[1]));
      cursor += 1;
    }
    if (values.length > 0) {
      attrs[key] = values;
      i = cursor - 1;
    } else {
      attrs[key] = "";
    }
  }
  return { attrs, error: null };
};

const normalizeInlineCode = (value) => {
  const trimmed = (value ?? "").trim();
  if (trimmed.startsWith("`") && trimmed.endsWith("`")) {
    return trimmed.slice(1, -1).trim();
  }
  return trimmed;
};

const sectionContent = (src, heading) => {
  const lines = src.split(/\r?\n/);
  const start = lines.findIndex((line) => line.trim() === `## ${heading}`);
  if (start === -1) return null;
  const end = lines.findIndex((line, index) =>
    index > start && /^##\s+/.test(line)
  );
  return lines.slice(start + 1, end === -1 ? lines.length : end).join("\n");
};

const hasSubstantiveContent = (content) => {
  if (!content) return false;
  const withoutEmptyTables = stripCodeBlocks(content)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => {
      if (line === "") return false;
      if (/^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line)) {
        return false;
      }
      if (/^\|\s*\|\s*\|/.test(line)) return false;
      if (
        /^\|\s*(Command \/ Test|Checklist Item|ID)\s*\|\s*(Result|Reason)\s*\|/i
          .test(line)
      ) {
        return false;
      }
      return true;
    })
    .join("\n");
  const cleaned = withoutEmptyTables
    .replace(/\|/g, " ")
    .replace(/[-:#`]/g, " ")
    .replace(/\b(None|N\/A|なし|未実施|command|result summary)\b/gi, " ")
    .trim();
  return /[A-Za-z0-9一-龠ぁ-んァ-ン]/.test(cleaned);
};

const referencesInclude = (attrs, path) =>
  Array.isArray(attrs.references) && attrs.references.includes(path);

const add = (items, file, message) => items.push({ file, message });

const validateFrontMatter = (file, attrs, errors) => {
  for (
    const key of [
      "title",
      "status",
      "draft_status",
      "qa_status",
      "risk",
      "created_at",
      "updated_at",
      "references",
      "related_issues",
      "related_prs",
    ]
  ) {
    if (!(key in attrs)) {
      add(errors, file, `missing front matter field: ${key}`);
    }
  }
  if ("qa_schema" in attrs && attrs.qa_schema !== QA_SCHEMA) {
    add(errors, file, `qa_schema must be ${QA_SCHEMA}`);
  }
  if (attrs.qa_status && !QA_STATUS_VALUES.includes(attrs.qa_status)) {
    add(
      errors,
      file,
      `qa_status must be one of ${QA_STATUS_VALUES.join(", ")}`,
    );
  }
  if (attrs.risk && !RISKS.includes(attrs.risk)) {
    add(errors, file, `risk must be one of ${RISKS.join(", ")}`);
  }
  if (!Array.isArray(attrs.references)) {
    add(errors, file, "references must be an array");
  }
};

const validateTestMatrix = (file, src, errors, warnings) => {
  const matrix = sectionContent(src, "Test Matrix");
  if (matrix === null) return;
  const rows = matrix
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|") && /AC-|INV-/.test(line));

  if (!rows.some((row) => /\bAC-\d{3}\b/.test(row))) {
    add(errors, file, "Test Matrix must include at least one AC- row");
  }

  for (const row of rows) {
    const cells = row.split("|").map((cell) => cell.trim()).filter(Boolean);
    const status = cells.at(-1);
    if (status && !TEST_MATRIX_STATUS_VALUES.includes(status)) {
      add(
        errors,
        file,
        `Test Matrix status must be one of ${
          TEST_MATRIX_STATUS_VALUES.join(", ")
        }`,
      );
    }
    if (status === "deferred") {
      add(warnings, file, "deferred Test Matrix rows must document a reason");
    }
  }
};

const validateTestPlan = async ({
  file,
  src,
  attrs,
  area,
  slug,
  errors,
  warnings,
}) => {
  const usesWhyFirstSchema = attrs.qa_schema === QA_SCHEMA;

  if (!["planned", "in-progress"].includes(attrs.qa_status)) {
    add(
      errors,
      file,
      "test-plan qa_status must be planned or in-progress",
    );
  }

  const requiredHeadings = [
    "Source of Intent",
    ...(usesWhyFirstSchema ? ["Decision Review Scope"] : []),
    "Quality Goal",
    "Acceptance Criteria",
    "Intent-derived Invariants",
    "Risk Assessment",
    "Test Strategy",
    "Test Matrix",
    "Manual QA Checklist",
    "Regression Checklist",
    "Out of Scope",
    "Open Questions",
  ];
  for (const heading of requiredHeadings) {
    if (sectionContent(src, heading) === null) {
      add(errors, file, `missing heading: ${heading}`);
    }
  }

  const intentPath = `_docs/intent/${area}/${slug}/decision.md`;
  const planPath = `_docs/plan/${area}/${slug}/plan.md`;
  if (!referencesInclude(attrs, intentPath)) {
    add(errors, file, `references must include ${intentPath}`);
  }
  if (await exists(planPath) && !referencesInclude(attrs, planPath)) {
    add(errors, file, `references must include existing plan ${planPath}`);
  }

  const ac = sectionContent(src, "Acceptance Criteria") ?? "";
  if (!/\bAC-\d{3}\b/.test(ac)) {
    add(errors, file, "Acceptance Criteria must include AC-001 style IDs");
  }

  if (
    usesWhyFirstSchema &&
    !sectionHasId(src, "Decision Review Scope", "DEC")
  ) {
    add(errors, file, "Decision Review Scope must include DEC-001 style IDs");
  }

  const invariants = sectionContent(src, "Intent-derived Invariants") ?? "";
  if (
    usesWhyFirstSchema &&
    !isExplicitNone(invariants) &&
    !/\bINV-\d{3}\b/.test(invariants)
  ) {
    add(
      errors,
      file,
      "Intent-derived Invariants must be None or include INV-001 style IDs",
    );
  } else if (!usesWhyFirstSchema && !/\bINV-\d{3}\b/.test(invariants)) {
    add(
      errors,
      file,
      "Intent-derived Invariants must include INV-001 style IDs",
    );
  }
  validateTestMatrix(file, src, errors, warnings);

  if (["High", "Critical"].includes(attrs.risk)) {
    const highRisk = sectionContent(src, "High-risk Checklist");
    if (highRisk === null) {
      add(errors, file, "Risk High/Critical requires High-risk Checklist");
    } else {
      for (const term of ["rollback", "recovery", "data safety", "security"]) {
        if (!new RegExp(term, "i").test(highRisk)) {
          add(errors, file, `High-risk Checklist must mention ${term}`);
        }
      }
    }
  }
};

const sectionHasId = (src, heading, prefix) =>
  new RegExp(`\\b${prefix}-\\d{3}\\b`).test(sectionContent(src, heading) ?? "");

const isNoneLike = (content) => {
  const cleaned = stripCodeBlocks(content ?? "")
    .replace(/\|/g, " ")
    .replace(/[-:#`]/g, " ")
    .trim();
  return cleaned === "" || /^(None|N\/A|なし)$/i.test(cleaned);
};

const isExplicitNone = (content) => {
  const cleaned = stripCodeBlocks(content ?? "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .trim();
  return /^(?:[-*]\s*)?(None|N\/A|なし)$/i.test(cleaned);
};

const validateVerification = ({
  file,
  src,
  attrs,
  area,
  slug,
  errors,
}) => {
  const usesWhyFirstSchema = attrs.qa_schema === QA_SCHEMA;
  const requiredHeadings = [
    "Summary",
    "Verification Verdict",
    "Commands Run",
    "Automated Test Results",
    "Manual QA Results",
    "Acceptance Criteria Coverage",
    ...(usesWhyFirstSchema ? ["Decision Conformance"] : []),
    "Invariant Coverage",
    "Deferred / Not Covered",
    "Residual Risks",
    "Follow-up TODOs",
  ];
  for (const heading of requiredHeadings) {
    if (sectionContent(src, heading) === null) {
      add(errors, file, `missing heading: ${heading}`);
    }
  }

  const testPlanPath = `_docs/qa/${area}/${slug}/test-plan.md`;
  const intentPath = `_docs/intent/${area}/${slug}/decision.md`;
  if (!referencesInclude(attrs, testPlanPath)) {
    add(errors, file, `references must include ${testPlanPath}`);
  }
  if (!referencesInclude(attrs, intentPath)) {
    add(errors, file, `references must include ${intentPath}`);
  }

  const verdictSection = sectionContent(src, "Verification Verdict") ?? src;
  const verdict = verdictSection.match(
    /\bVerdict:\s*(PASS|PARTIAL|FAIL|BLOCKED)\b/,
  )
    ?.[1];
  if (!verdict || !VERDICTS.includes(verdict)) {
    add(errors, file, `Verdict must be one of ${VERDICTS.join(", ")}`);
  } else {
    const expectedStatus = VERDICT_STATUS[verdict];
    if (attrs.qa_status !== expectedStatus) {
      add(
        errors,
        file,
        `qa_status "${attrs.qa_status}" does not match Verdict "${verdict}"; expected "${expectedStatus}"`,
      );
    }
  }
  if (!["verified", "partial", "failed", "blocked"].includes(attrs.qa_status)) {
    add(
      errors,
      file,
      "verification qa_status must be verified, partial, failed, or blocked",
    );
  }

  const residual = sectionContent(src, "Residual Risks") ?? "";
  const followUps = sectionContent(src, "Follow-up TODOs") ?? "";
  if (verdict === "PASS" && !isNoneLike(residual)) {
    add(
      errors,
      file,
      "PASS verification must have empty or None residual risks",
    );
  }
  if (
    ["PARTIAL", "FAIL", "BLOCKED"].includes(verdict ?? "") &&
    !hasSubstantiveContent(residual) &&
    !hasSubstantiveContent(followUps)
  ) {
    add(
      errors,
      file,
      "PARTIAL/FAIL/BLOCKED requires residual risks or follow-up TODOs",
    );
  }

  if (!sectionHasId(src, "Acceptance Criteria Coverage", "AC")) {
    add(errors, file, "Acceptance Criteria Coverage must include AC- IDs");
  }

  if (
    usesWhyFirstSchema &&
    !sectionHasId(src, "Decision Conformance", "DEC")
  ) {
    add(errors, file, "Decision Conformance must include DEC- IDs");
  }

  const invariantCoverage = sectionContent(src, "Invariant Coverage") ?? "";
  if (
    usesWhyFirstSchema &&
    !isExplicitNone(invariantCoverage) &&
    !sectionHasId(src, "Invariant Coverage", "INV")
  ) {
    add(errors, file, "Invariant Coverage must be None or include INV- IDs");
  } else if (
    !usesWhyFirstSchema &&
    !sectionHasId(src, "Invariant Coverage", "INV")
  ) {
    add(errors, file, "Invariant Coverage must include INV- IDs");
  }
  if (
    !hasSubstantiveContent(sectionContent(src, "Commands Run")) &&
    !hasSubstantiveContent(sectionContent(src, "Manual QA Results"))
  ) {
    add(
      errors,
      file,
      "Commands Run or Manual QA Results must contain substantive evidence",
    );
  }
};

const parseTodoTasks = (src) => {
  const stripped = stripCodeBlocks(src);
  const tasks = [];
  let current = null;
  let currentField = null;
  const flush = () => {
    if (current) tasks.push(current);
    current = null;
    currentField = null;
  };

  for (const line of stripped.split(/\r?\n/)) {
    const field = line.match(TODO_FIELD_RE);
    if (field?.[1] === "Title") {
      flush();
      current = { fields: { Title: field[2].trim() } };
      currentField = "Title";
      continue;
    }
    if (!current) continue;
    if (field) {
      current.fields[field[1].trim()] = field[2].trim();
      currentField = field[1].trim();
      continue;
    }
    if (currentField && (/^\s+/.test(line) || line.trim() === "")) {
      current.fields[currentField] = `${
        current.fields[currentField] ?? ""
      }\n${line}`.trimEnd();
    }
  }
  flush();
  return tasks;
};

const validateTodoConsistency = async (errors) => {
  const tasks = parseTodoTasks(await Deno.readTextFile(TODO_FILE));
  for (const task of tasks) {
    const label = task.fields.ID ?? task.fields.Title ?? "(unknown task)";
    const risk = task.fields.Risk;
    const intent = normalizeInlineCode(task.fields.Intent);

    for (const field of ["QA", "Verification"]) {
      const path = normalizeInlineCode(task.fields[field]);
      if (!path || path === "None") continue;
      if (!QA_PATH_RE.test(path)) {
        add(errors, TODO_FILE, `${label}: ${field} path is not canonical`);
        continue;
      }
      if (!await exists(path)) {
        add(
          errors,
          TODO_FILE,
          `${label}: ${field} file does not exist: ${path}`,
        );
        continue;
      }
      const src = await Deno.readTextFile(path);
      const { attrs, error } = parseFrontMatter(src);
      if (error || !attrs) {
        add(errors, path, error ?? "missing front matter");
        continue;
      }
      if (intent !== "None" && !referencesInclude(attrs, intent)) {
        add(
          errors,
          path,
          `${field} references must include TODO Intent ${intent}`,
        );
      }
      if (risk && attrs.risk !== risk) {
        add(errors, path, `${field} risk must match TODO Risk ${risk}`);
      }
    }
  }
};

const report = (prefix, items, logger) => {
  const grouped = new Map();
  for (const item of items) {
    if (!grouped.has(item.file)) grouped.set(item.file, []);
    grouped.get(item.file).push(item.message);
  }
  for (const [file, messages] of grouped) {
    logger(`${prefix}: ${file}`);
    for (const message of messages) logger(`  - ${message}`);
  }
};

const parseArgs = (args) => {
  if (args.length === 0) return { roots: ["_docs/qa"], fixtureMode: false };
  if (args[0] === "--fixture") {
    return { roots: args.slice(1), fixtureMode: true };
  }
  return { roots: args, fixtureMode: false };
};

const collectMarkdownFiles = async function* (roots) {
  for (const root of roots) {
    const kind = await fileOrDir(root);
    if (kind === "file") {
      if (root.endsWith(".md")) yield normalizePath(root);
      continue;
    }
    yield* walkFiles(root, (path) => path.endsWith(".md"));
  }
};

const effectiveQaMatch = ({ file, src, attrs, fixtureMode, errors }) => {
  const effectivePath = fixtureMode && typeof attrs.fixture_path === "string"
    ? normalizePath(attrs.fixture_path)
    : file;
  if (
    effectivePath.includes("_docs/archives/qa/") ||
    /(^|\/)archives\/qa\//.test(effectivePath)
  ) {
    add(errors, file, "QA docs must not be placed under archives/qa");
    return null;
  }
  const match = effectivePath.match(QA_PATH_RE);
  if (match) return match;
  if (!fixtureMode) {
    add(
      errors,
      file,
      "QA path must match _docs/qa/<Area>/<slug>/test-plan.md or verification.md",
    );
    return null;
  }

  const kind = sectionContent(src, "Verification Verdict") === null
    ? "test-plan"
    : "verification";
  return [effectivePath, "Fixture", "fixture", kind];
};

const run = async () => {
  const errors = [];
  const warnings = [];
  const { roots, fixtureMode } = parseArgs(Deno.args);
  const inScope = makeInScope(await loadScope());

  if (roots.length === 0) {
    add(errors, "(args)", "--fixture requires at least one path");
  }

  for await (const file of collectMarkdownFiles(roots)) {
    if (!inScope(file)) continue;
    const src = await Deno.readTextFile(file);
    const { attrs, error } = parseFrontMatter(src);
    if (error || !attrs) {
      add(errors, file, error ?? "missing front matter");
      continue;
    }

    const match = effectiveQaMatch({ file, src, attrs, fixtureMode, errors });
    if (!match) continue;
    const [, area, slug, kind] = match;

    validateFrontMatter(file, attrs, errors);
    if (kind === "test-plan") {
      await validateTestPlan({
        file,
        src,
        attrs,
        area,
        slug,
        errors,
        warnings,
      });
    } else {
      validateVerification({ file, src, attrs, area, slug, errors });
    }
  }

  if (!fixtureMode) {
    await validateTodoConsistency(errors);
  }

  report("WARN", warnings, console.warn);
  if (errors.length) {
    report("ERROR", errors, console.error);
    Deno.exit(1);
  }
};

run().catch((err) => {
  console.error(err);
  Deno.exit(1);
});
