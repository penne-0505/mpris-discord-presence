// 段階的導入向けの共有スコープ解決: 既定では「導入以降に追加された docs」だけを
// 検証対象へ絞るための母集合を一箇所で決める。env 未設定なら null を返し、
// 全走査の従来挙動を保つ（後方互換）。

const DEFAULT_DIFF_FILTER = "A";
const DIFF_FILTER_RE = /^[ACDMRTUXB]+$/;

const normalizePath = (path) => {
  const segments = [];
  for (const segment of path.replaceAll("\\", "/").split("/")) {
    if (segment === "" || segment === ".") continue;
    if (segment === "..") segments.pop();
    else segments.push(segment);
  }
  return segments.join("/");
};

// env 読み取りは権限が無くても安全側（未設定扱い = 全走査）に倒す。
const readEnv = (key) => {
  try {
    return Deno.env.get(key);
  } catch {
    return undefined;
  }
};

const fromPathList = (raw) =>
  raw
    .split(/[\n:]+/)
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map(normalizePath);

const diffFilter = () => {
  const raw = readEnv("DD_SCOPE_DIFF_FILTER")?.trim();
  if (raw === undefined || raw === "") return DEFAULT_DIFF_FILTER;
  if (!DIFF_FILTER_RE.test(raw)) {
    throw new Error(
      `scope: DD_SCOPE_DIFF_FILTER must contain only git diff-filter letters (${raw})`,
    );
  }
  return raw;
};

const fromGitDiff = async (base) => {
  const filter = diffFilter();
  let output;
  try {
    const command = new Deno.Command("git", {
      args: [
        "diff",
        "--name-only",
        `--diff-filter=${filter}`,
        `${base}...HEAD`,
      ],
      stdout: "piped",
      stderr: "piped",
    });
    output = await command.output();
  } catch (err) {
    throw new Error(
      `scope: DD_SCOPE_BASE is set but "git" could not run (need --allow-run=git): ${err.message}`,
    );
  }
  if (!output.success) {
    const stderr = new TextDecoder().decode(output.stderr).trim();
    throw new Error(
      `scope: git diff against base "${base}" failed (exit ${output.code}): ${stderr}`,
    );
  }
  return new TextDecoder()
    .decode(output.stdout)
    .split(/\r?\n/)
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map(normalizePath);
};

// 検証対象の母集合を返す。
// - DD_SCOPE_PATHS: 改行 / コロン区切りの明示パスリスト（テスト・CI 自前計算向け）。
// - DD_SCOPE_BASE: git ref。既定では `<ref>...HEAD` で追加されたファイルのみ。
// - DD_SCOPE_DIFF_FILTER: DD_SCOPE_BASE 使用時の git diff-filter。既定は A。
// - いずれも未設定: null（= 全走査）。
// 優先順位は DD_SCOPE_PATHS > DD_SCOPE_BASE > null。
export const loadScope = async () => {
  const paths = readEnv("DD_SCOPE_PATHS");
  if (paths !== undefined && paths.trim() !== "") {
    return new Set(fromPathList(paths));
  }
  const base = readEnv("DD_SCOPE_BASE");
  if (base !== undefined && base.trim() !== "") {
    return new Set(await fromGitDiff(base.trim()));
  }
  return null;
};

// scope が null（= 全走査）のときは全ファイルが対象。
export const makeInScope = (scope) => (path) =>
  scope === null || scope.has(normalizePath(path));

export { normalizePath };
