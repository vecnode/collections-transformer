# Issue #7 Refactor Plan

## Goal
Refactor legacy helper utilities into modular, domain-focused client utilities while preserving current behavior.

## Constraints
- No behavior regressions in existing pages/components.
- Keep current runtime stack (Next.js + JavaScript) stable in this phase.
- Preserve existing helper API surface through a compatibility layer.

## Execution Plan
1. Baseline mapping
- Inventory all usages of `client/src/_helpers/utills.js`.
- Classify helper functions by domain (collections, formatting, analysis, errors, React debugging, analyser changes).

2. Modular extraction
- Move helper logic into focused modules under `client/src/lib/`:
  - `analysis/validation.js`
  - `collections/items.js`
  - `export/csv.js`
  - `format/labels.js`
  - `format/text.js`
  - `time/date.js`
  - `errors/contentFilter.js`
  - `react/debug.js`
  - `analyser/changes.js`

3. Compatibility and migration
- Reduce `client/src/_helpers/utills.js` to a thin compatibility barrel.
- Migrate existing imports in components/pages to new module paths.

4. Verification
- Run lint and smoke checks in the client.
- Confirm no import errors and no functional regressions in affected UI flows.

5. Follow-up (next iteration)
- Add targeted client unit tests for critical pure helpers.
- Incrementally introduce TypeScript for helper modules (`.ts`) once test safety net is in place.

## Acceptance Mapping
- Monolithic helper file reduced to compatibility layer.
- Domain-specific modules introduced under a clear folder structure.
- Components import focused modules instead of a catch-all utility file.
- Existing functionality preserved.
