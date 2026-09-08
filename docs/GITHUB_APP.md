# Compart GitHub App: Bot Behavior

> One agent, two authorities. `Consult` explains and files Issues. `Work` repairs and opens PRs. The reasoning engine is identical; only what it may touch differs.

## 1. Events handled

| Event | Behavior |
|---|---|
| `pull_request.opened/synchronize/reopened` | Full pipeline on the exact PR head SHA (fetched via `pull/N/head`); falls back to the tracked branch with an explicit `[checkout: tracked branch, PR head unfetchable]` marker — never silently claimed |
| `issue_comment.created` with `@compart` | Re-runs the pipeline on the PR |
| `issue_comment.created` with `@compart explain` | Posts read-only impact reasoning; modifies nothing |
| Other comments, bot comments, non-PR comments | Ignored |
| `installation.*` / `installation_repositories.*` | Persist record → clone → Day-0 index → `INDEXED`, then `READY` once surfaced |
| `external.change.*` | Watch-loop findings enter the shared pipeline |

## 2. PR comment anatomy

Every PR comment opens with a summary (what changed, who it affects, evidence-grounded confidence — `high` only when verified green), followed by the trust body or findings, a mermaid `change → files → verification` diagram when findings exist, and a footer with the reviewed commit SHA plus a `@compart` re-run note.

Findings carry severity badges: **P0** needs a human (unrepairable/quarantined), **P1** is repairable. Verified repairs keep `[VERIFIED]` semantics: real command, real exit 0, zero unintended files — otherwise the badge never appears.

## 3. Bot configuration (`.compart/config.yaml`)

```yaml
bot:
  mode: consult            # consult = report only, work = repair (default)
  pr_review: true
  pr_auto_fix: false
  external_auto_fix: false
  auto_fix_providers: []   # empty = all providers allowed
  ignore_paths: ["docs/**", "*.md"]
  exclude_labels: ["dependencies"]
  always_report_clean: true
  inline_comments: true
```

PRs touching only `ignore_paths`, or carrying an `exclude_labels` label, are skipped with a recorded reason. Unknown `mode` values fall back to `work`.

## 4. Adoption ladder

New installations start in `consult`: accurate Issues build trust in the reasoning before anyone grants repair authority. Flip one line to `work` when ready — the engine never changes.

## 5. Deployment

See [DEPLOY.md](DEPLOY.md) for the webhook secret requirement, environment table, Docker image, `--watch` background monitoring, volumes, and security notes.
