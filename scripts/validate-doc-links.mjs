// Deno版 Markdown link / front-matter reference validator: npm / remote import 依存なし

import { loadScope, makeInScope } from "./scope.mjs";

const DOC_ROOTS = ["_docs", "_evals"];
const ROOT_FILES = ["README.md", "AGENTS.md", "TODO.md", "QUICKSTART.md"];
const ARCHIVE_TYPES = ["draft", "plan", "survey"];
const FORBIDDEN_ARCHIVE_TYPES = ["intent", "qa", "guide", "reference"];
const ROOT_RELATIVE_PREFIXES = [
  "_docs/",
  "_evals/",
  ".agents/",
  ".claude/",
  ".github/",
  "scripts/",
];
const ROOT_RELATIVE_FILES = [
  "README.md",
  "AGENTS.md",
  "TODO.md",
  "QUICKSTART.md",
  "LICENSE.txt",
];
const FIXTURE_ROOT = "_evals/validator-fixtures/";

const normalizePath = (path) => {
  const segments = [];
  for (const segment of path.replaceAll("\\", "/").split("/")) {
    if (segment === "" || segment === ".") continue;
    if (segment === "..") {
      segments.pop();
    } else {
      segments.push(segment);
    }
  }
  return segments.join("/");
};

const dirname = (path) => {
  const normalized = normalizePath(path);
  const index = normalized.lastIndexOf("/");
  return index === -1 ? "." : normalized.slice(0, index);
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
    await Deno.stat(path);
    return true;
  } catch (err) {
    if (err instanceof Deno.errors.NotFound) return false;
    throw err;
  }
};

const isDirectory = async (path) => {
  try {
    const stat = await Deno.stat(path);
    return stat.isDirectory;
  } catch (err) {
    if (err instanceof Deno.errors.NotFound) return false;
    throw err;
  }
};

const isExternal = (target) =>
  /^[a-z][a-z0-9+.-]*:/i.test(target) ||
  target.startsWith("//");

const isTemplatePlaceholder = (target) => /<[^>]+>/.test(target);
const isValidatorFixture = (file) => file.startsWith(FIXTURE_ROOT);

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
  if (lines[0] !== "---") return { attrs: null, error: null };
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

const normalizeLinkTarget = (raw) => {
  let target = raw.trim();
  if (target.startsWith("<")) {
    const close = target.indexOf(">");
    target = close === -1 ? target.slice(1) : target.slice(1, close);
  } else {
    target = target.split(/\s+/)[0];
  }
  return target;
};

const referenceDefinitions = (body) => {
  const refs = new Map();
  const defRe = /^\s{0,3}\[([^\]]+)]:\s*(\S+(?:\s+\S+)*)\s*$/gm;
  for (const match of body.matchAll(defRe)) {
    refs.set(match[1].trim().toLowerCase(), normalizeLinkTarget(match[2]));
  }
  return refs;
};

const extractInlineMarkdownTargets = (body) => {
  const targets = [];
  const linkRe = /!?\[[^\]]*]\(([^)]+)\)/g;
  for (const match of body.matchAll(linkRe)) {
    targets.push(normalizeLinkTarget(match[1]));
  }
  return targets;
};

const extractReferenceMarkdownTargets = (file, body, errors) => {
  const targets = [];
  const refs = referenceDefinitions(body);
  for (const target of refs.values()) targets.push(target);

  const usageRe = /!?\[([^\]]+)]\[([^\]]*)]/g;
  for (const match of body.matchAll(usageRe)) {
    const label = match[2].trim() === "" ? match[1].trim() : match[2].trim();
    const target = refs.get(label.toLowerCase());
    if (target === undefined) {
      errors.push({
        file,
        message: `missing reference-style link definition: ${label}`,
      });
      continue;
    }
    targets.push(target);
  }
  return targets;
};

const extractMarkdownTargets = (file, src, errors) => {
  const body = stripCodeBlocks(src);
  return [
    ...extractInlineMarkdownTargets(body),
    ...extractReferenceMarkdownTargets(file, body, errors),
  ];
};

const splitTarget = (target) => {
  const [beforeAnchor, rawAnchor = ""] = target.split("#");
  const clean = beforeAnchor.split("?")[0];
  return {
    clean,
    anchor: rawAnchor === "" ? "" : rawAnchor.split("?")[0],
  };
};

const isRootRelative = (target) =>
  ROOT_RELATIVE_PREFIXES.some((prefix) => target.startsWith(prefix)) ||
  ROOT_RELATIVE_FILES.includes(target);

const resolveTarget = (fromFile, target) => {
  if (isExternal(target)) return null;
  const { clean } = splitTarget(target);
  if (clean === "") return normalizePath(fromFile);
  let decoded = clean;
  try {
    decoded = decodeURIComponent(clean);
  } catch {
    decoded = clean;
  }
  if (decoded.startsWith("/")) return null;
  const base = isRootRelative(decoded) ? "." : dirname(fromFile);
  return normalizePath(`${base}/${decoded}`);
};

const decodeAnchor = (anchor) => {
  try {
    return decodeURIComponent(anchor);
  } catch {
    return anchor;
  }
};

const slugifyHeading = (heading) =>
  heading
    .replace(/<[^>]+>/g, "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\[([^\]]+)]\([^)]+\)/g, "$1")
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, "-");

const headingAnchors = async (file, cache) => {
  if (cache.has(file)) return cache.get(file);
  const src = await Deno.readTextFile(file);
  const anchors = new Set();
  const counts = new Map();
  for (const line of stripCodeBlocks(src).split(/\r?\n/)) {
    const match = line.match(/^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/);
    if (!match) continue;
    const base = slugifyHeading(match[1]);
    if (base === "") continue;
    const count = counts.get(base) ?? 0;
    counts.set(base, count + 1);
    anchors.add(count === 0 ? base : `${base}-${count}`);
  }
  cache.set(file, anchors);
  return anchors;
};

const validateLocalTarget = async (fromFile, target, errors, anchorCache) => {
  if (isTemplatePlaceholder(target)) return;
  const resolved = resolveTarget(fromFile, target);
  if (!resolved) return;
  if (!await exists(resolved)) {
    errors.push({
      file: fromFile,
      message: `missing local link target: ${target} -> ${resolved}`,
    });
    return;
  }
  const { anchor } = splitTarget(target);
  if (anchor === "" || !resolved.endsWith(".md")) return;
  const anchors = await headingAnchors(resolved, anchorCache);
  const slug = slugifyHeading(decodeAnchor(anchor));
  if (!anchors.has(slug)) {
    errors.push({
      file: fromFile,
      message: `missing markdown anchor: ${target} -> ${resolved}#${slug}`,
    });
  }
};

const markdownFiles = async () => {
  const files = [];
  for (const root of DOC_ROOTS) {
    for await (const file of walkFiles(root, (path) => path.endsWith(".md"))) {
      files.push(file);
    }
  }
  for (const file of ROOT_FILES) {
    if (await exists(file)) files.push(file);
  }
  return files.sort();
};

const hasMarkdown = async (dir) => {
  for await (const _file of walkFiles(dir, (path) => path.endsWith(".md"))) {
    return true;
  }
  return false;
};

const collectIntentReferences = async () => {
  const refs = new Set();
  for await (
    const file of walkFiles("_docs/intent", (path) => path.endsWith(".md"))
  ) {
    const src = await Deno.readTextFile(file);
    const { attrs } = parseFrontMatter(src);
    if (Array.isArray(attrs?.references)) {
      for (const ref of attrs.references) {
        if (typeof ref !== "string") continue;
        const resolved = resolveTarget(file, ref);
        if (resolved) refs.add(resolved);
      }
    }
  }
  return refs;
};

const validateArchiveInvariants = async (errors, inScope, scoped) => {
  // ディレクトリ存在自体を咎める検査は、スコープ有効時は既存構造を判定しないため抑止する。
  if (!scoped) {
    for (const type of FORBIDDEN_ARCHIVE_TYPES) {
      const dir = `_docs/archives/${type}`;
      if (await isDirectory(dir)) {
        errors.push({
          file: dir,
          message:
            "archive directories are only allowed for draft, plan, and survey",
        });
      }
    }
  }

  const intentRefs = await collectIntentReferences();
  for await (
    const file of walkFiles("_docs/archives", (path) => path.endsWith(".md"))
  ) {
    if (!inScope(file)) continue;
    const parts = file.split("/");
    const [, archives, type, area, slug] = parts;
    if (
      archives !== "archives" || !ARCHIVE_TYPES.includes(type) || !area || !slug
    ) {
      errors.push({
        file,
        message:
          "archive path must match _docs/archives/{draft,plan,survey}/<Area>/<slug>/...",
      });
      continue;
    }

    const src = await Deno.readTextFile(file);
    const { attrs, error } = parseFrontMatter(src);
    if (error || !attrs) {
      errors.push({
        file,
        message: error ?? "archived document must have parseable front matter",
      });
    }

    const intent = `_docs/intent/${area}/${slug}/decision.md`;
    if (!await exists(intent) && !intentRefs.has(file)) {
      errors.push({
        file,
        message: `archived document requires corresponding intent: ${intent}`,
      });
    }

    const liveDir = `_docs/${type}/${area}/${slug}`;
    if (await hasMarkdown(liveDir)) {
      errors.push({
        file,
        message:
          `live ${type} document still exists for archived ${area}/${slug}`,
      });
    }
  }
};

const validateQaInvariants = async (errors, inScope) => {
  for await (
    const file of walkFiles("_docs/qa", (path) => path.endsWith(".md"))
  ) {
    if (!inScope(file)) continue;
    const match = file.match(
      /^_docs\/qa\/([A-Za-z][A-Za-z0-9-]*)\/([a-z0-9]+(?:-[a-z0-9]+)*)\/(test-plan|verification)\.md$/,
    );
    if (!match) {
      errors.push({
        file,
        message:
          "QA path must match _docs/qa/<Area>/<slug>/test-plan.md or verification.md",
      });
      continue;
    }

    const [, area, slug, kind] = match;
    if (kind === "verification") {
      const testPlan = `_docs/qa/${area}/${slug}/test-plan.md`;
      if (!await exists(testPlan)) {
        errors.push({
          file,
          message: `verification requires matching test plan: ${testPlan}`,
        });
      }
    }
  }
};

const validateGuideReferenceWarnings = async (warnings, inScope) => {
  for (const type of ["guide", "reference"]) {
    for await (
      const file of walkFiles(`_docs/${type}`, (path) => path.endsWith(".md"))
    ) {
      if (!inScope(file)) continue;
      const src = await Deno.readTextFile(file);
      const { attrs } = parseFrontMatter(src);
      if (attrs?.status !== "active") continue;
      const refs = Array.isArray(attrs.references) ? attrs.references : [];
      const hasRelatedRef = refs.some((ref) =>
        typeof ref === "string" &&
        (ref.includes("/intent/") ||
          ref.includes("../intent/") ||
          ref.includes("/guide/") ||
          ref.includes("/reference/") ||
          ref.includes("../guide/") ||
          ref.includes("../reference/"))
      );
      if (!hasRelatedRef) {
        warnings.push({
          file,
          message:
            "active guide/reference should reference related intent, guide, or reference",
        });
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

const run = async () => {
  const errors = [];
  const warnings = [];
  const scope = await loadScope();
  const inScope = makeInScope(scope);
  const scoped = scope !== null;
  const files = (await markdownFiles()).filter(inScope);
  const anchorCache = new Map();

  for (const file of files) {
    const src = await Deno.readTextFile(file);
    for (const target of extractMarkdownTargets(file, src, errors)) {
      await validateLocalTarget(file, target, errors, anchorCache);
    }

    const { attrs, error } = parseFrontMatter(src);
    if (error) {
      errors.push({ file, message: error });
      continue;
    }
    if (attrs && "references" in attrs) {
      if (!Array.isArray(attrs.references)) {
        errors.push({
          file,
          message: "front matter references must be an array",
        });
      } else if (!isValidatorFixture(file)) {
        for (const ref of attrs.references) {
          if (typeof ref !== "string") {
            errors.push({
              file,
              message: "front matter references must contain only strings",
            });
            continue;
          }
          await validateLocalTarget(file, ref, errors, anchorCache);
        }
      }
    }
  }

  await validateArchiveInvariants(errors, inScope, scoped);
  await validateQaInvariants(errors, inScope);
  await validateGuideReferenceWarnings(warnings, inScope);

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
