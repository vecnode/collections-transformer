# Issue #9 TypeScript Migration (Incremental)

## Scope delivered in this branch

1. TypeScript tooling enabled for the client
- Added `client/tsconfig.json` with relaxed settings (`strict: false`, `allowJs: true`) for phased adoption.
- Added client script: `npm run typecheck` (`tsc --noEmit`).
- Added TypeScript dependencies and React/Node type packages.

2. CI check for type safety
- Added workflow `.github/workflows/client-typecheck.yml`.
- Runs `npm ci` and `npm run typecheck` in `client/` on PRs and pushes affecting client files.

3. Shared domain models
- Added `client/src/types/models.ts` and `client/src/types/index.ts`.
- Introduced shared types for `User`, `Dataset`, `CollectionItem`, `Labelset`, `Label`, `Analyser`, `PredictionResult`, and content filter errors.

4. Phase 1 helper migration (high-value, low-risk)
- Migrated helper modules from JS to TS:
  - `client/src/lib/items.ts`
  - `client/src/lib/labels.ts`
  - `client/src/lib/date.ts`
  - `client/src/lib/contentFilter.ts`
- Added explicit function signatures and narrowed return types where appropriate.

5. Phase 2 context migration
- Migrated auth context from JS to TSX:
  - `client/src/contexts/AuthContext.tsx`
- Added typed context contract (`AuthContextValue`) and typed auth action results.

6. Phase 3 complex component contract
- Migrated complex list component to TSX with typed props:
  - `client/src/components/itemDynamicList.tsx`
- Added a typed prop contract using shared models.
- Migrated `client/src/components/datasetLabeller.tsx` and typed its props against shared models.

## Migration policy adopted
- New client files should use TypeScript by default (`.ts` / `.tsx`).
- Existing JavaScript files are converted using touch-and-migrate when making non-trivial updates.
- Keep strictness relaxed initially; tighten progressively in follow-up issues.

## Follow-up suggestions
- Convert additional high-complexity components (`overviewanalyser`, `workspace` page flow).
- Add typed API client wrapper and replace ad-hoc `fetch` result handling.
- Enable stricter compiler options in stages (`noImplicitAny`, then `strict`).
