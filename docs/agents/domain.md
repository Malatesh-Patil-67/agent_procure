# Domain Docs

How engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists: it points at one `CONTEXT.md` per context.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If any of these files do not exist, proceed silently. The `/domain-modeling` skill creates them when terms or decisions are resolved.

## File structure

This is a single-context repo: use a root `CONTEXT.md` and `docs/adr/` for architecture decision records.

## Use the glossary's vocabulary

When naming a domain concept, use the term defined in `CONTEXT.md`. If it does not exist, reconsider the term or record the gap for `/domain-modeling`.

## Flag ADR conflicts

If a proposed change contradicts an existing ADR, surface the conflict explicitly rather than silently overriding it.
