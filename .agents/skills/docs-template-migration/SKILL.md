---
name: docs-template-migration
description: Integrate a newer pinned release of this docs-driven template into an existing customized repository. Use after first-time adoption when a recommended upstream tag changes standards, validators, paired skills, hooks, CI, template meta-work, or document schemas. Do not use for first-time adoption or project-local schema edits without an upstream release.
---

# Docs-Driven Template Migration

Treat every update as a provenance-locked three-way migration:

- `B`: the upstream template revision previously adopted by the project.
- `U`: the recommended upstream release tag selected for this migration,
  resolved to its full commit SHA.
- `P`: the project snapshot at the owner-approved migration cutoff, represented
  by HEAD plus staged, unstaged, and untracked cutoff evidence.

Release tags name recommended update units. Full SHAs identify their exact
content. Never compare only against a moving branch tip, and stop if a recorded
tag resolves to a different commit.

The default provenance record is `docs-template.lock.json`, created from
`docs-template.lock.example.json`. It records template provenance only; schema
adoption and deferred work belong in the project's migration verification.

## Legacy bootstrap for pre-v1.0.0 repositories

A repository adopted before `v1.0.0` may have neither a release tag in its
history, a provenance lock, nor a local copy of this skill. It may migrate
directly to any selected release `U >= v1.0.0`; it does not need an intermediate
`v1.0.0` migration. Use the repository's own rules as the safety boundary,
review the skill shipped by `U` as external input, reconstruct the last adopted
template commit `B` from repository history, adoption records, and matching
upstream blobs, and obtain owner confirmation before writes. If `B` cannot be
identified without guessing, stop and report the missing evidence. After the
compatibility migration passes, create the first lock at `U`; later updates use
the normal tag-to-tag path.

## Procedure

### 1. Freeze the project cutoff

Read repository rules, inspect the current branch, HEAD, dirty paths, and
concurrent work before editing. Record whether the owner wants the migration in
the active tree or an isolated worktree. Give parallel writers non-overlapping
path ownership. Record `P` as the HEAD SHA plus the staged, unstaged, and
untracked manifest. For every in-scope dirty path, preserve its cutoff content
hash or cutoff diff.

Completion criterion: `P` is reproducible from HEAD plus cutoff evidence; the
cutoff time, dirty contents, destination mode, and parallel ownership are
explicit, and later changes can be distinguished from migration changes.

### 2. Lock provenance

Read `docs-template.lock.json` and confirm its source, tag, and full commit SHA.
For the legacy bootstrap path, use the confirmed untagged full SHA for `B` and
defer creation of the first lock until `U` has passed compatibility
verification. Resolve the selected `U` tag to a full commit SHA and record both
values; do not accept a branch name or moving tip as `U`.

Read the local migration skill when present and the version shipped by `U`.
Existing project rules and any local skill control safety until the migration
is complete. If the local skill is absent, do not install or trust the upstream
skill before reviewing it. Treat every unmerged upstream branch as a separate
migration lane.

Completion criterion: exactly one `B..U` range is selected; source, the `B`
identity, and the `U` tag plus full SHA are explicit; included and excluded
branch heads are recorded; tag resolution matches the recorded SHA; and
ambiguity stops the migration before writes.

### 3. Build the three-way inventory

Compare the upstream delta `B -> U` with the project delta `B -> P snapshot`.
Do not treat `P` as a commit when the cutoff includes dirty or untracked files.
Classify every path in the union on two independent axes:

- upstream delta: unchanged, added, modified, or removed;
- project relation: upstream-owned unmodified, customized shared, or
  project-only.

Flag template-self meta-work and schema-affected paths separately. Assign
exactly one resolution to every path: apply, merge, keep, remove, or defer. An
upstream deletion is not authorization to delete a project record.

Completion criterion: every path in both deltas has both classifications, one
resolution, and a rationale; no customization, meta-work decision, schema
transition, or removal is implicit.

### 4. Establish the migration contract

Use the repository's preparation and QA workflow when required. Record current
validator results before importing new validators. Review imported skills,
hooks, and scripts before executing or trusting them.

Acceptance criteria must cover provenance, customization, meta-work, schema
transition, concurrent-work isolation, and verification. Include agent
misbehavior checks for branch mixing, blind replacement, premature lock
advancement, and bulk schema edits.

Completion criterion: baseline failures are separated from migration
regressions, and every destructive or semantic operation has owner authority.

### 5. Integrate in gates

1. Import validators and fixtures in legacy-compatible mode when the selected
   release supports it. If it does not, make the incompatibility and migration
   order explicit before changing live documents.
2. Run imported validators against unchanged project docs before schema edits.
3. Merge standards, templates, paired skill trees, hooks, CI, and shared root
   docs path by path. Never replace a customized shared file wholesale.
4. Remove template-self meta-work only after its rules are absorbed elsewhere,
   provenance is proven, references are resolved, and deletion is authorized.
5. Classify legacy docs as current, migrate-now, or deferred. Migrate semantic
   edits; do not force schema conversion for link, typo, or metadata fixes.
6. Reclassify code anchors semantically: decision rationale points to `DEC-*`;
   only results required across every valid implementation point to `INV-*`.
7. Map every legacy ID to retained INV, DEC, delegated canonical authority,
   superseded history, or removal with owner authority. Do not renumber retained
   IDs. Preserve prior verification commands and results as historical evidence.
8. Confirm every schema marker is accepted by frontmatter, intent, and QA
   validators before migrating live documents.
9. Enable strict CI enforcement only after the selected schema target is
   satisfied.
10. Advance `docs-template.lock.json` from `B` to `U` only after `U` files are
    reconciled and the compatibility checks pass. Treat the lock update as the
    final migration write, then verify its tag and full SHA during closure.
    Record a deferred strict schema migration separately; never leave the lock
    pointing to `B` after `U` files have become the reconciled project baseline.

Completion criterion: every completed gate passes relative to the baseline. A
deferred gate has owner-authorized rationale, an explicit follow-up, and a
non-PASS verdict; every legacy and meta-work path has a final state; and the
lock identifies the upstream revision actually integrated.

### 6. Verify closure

Run the repository wrapper, validator fixtures, markdown lint, hook tests,
paired-skill comparison, provenance-lock review, diff checks, and
project-specific regression tests. Reconcile the final diff with the inventory
and prove that each project customization was preserved or intentionally
changed. Run the repository's QA review when required and record only commands
actually executed.

Completion criterion: no inventory path is unresolved, no parallel branch or
post-cutoff file was silently included, failures are not new or unexplained,
the lock resolves to the integrated `U` commit, and each migration-stage verdict
matches the evidence.

## Reporting Boundary

Report compatibility migration and strict schema migration separately. Never
collapse a staged or partially deferred result into full completion. Report the
full SHA for both `B` and `U`, and the release tag wherever one exists.
