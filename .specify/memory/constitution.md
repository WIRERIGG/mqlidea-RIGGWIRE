<!--
Sync Impact Report
- Version change: template -> 1.0.0 (first ratification)
- Principles added: I Honest, early diagnostics; II Sturdy platform API; III No MetaQuotes text or code;
  IV Read-only toward MetaTrader; V Every gate stays green
- Sections added: Repository Constraints, Development Workflow, Governance
- Templates: plan-template.md "Constitution Check" reads this file at plan time; no template edits needed
- Deferred: none
Every rule below already exists in CLAUDE.md or the owner's standing instructions; this file gathers
them, it adds none.
-->
# mqlidea-RIGGWIRE Constitution

## Core Principles

### I. Honest, early diagnostics
The plugin helps real MQL4/MQL5 projects: it reports errors early and inline, and it never claims more
than it can see.
- A diagnostic must be true of what MetaEditor compiles. False positives are bugs, and the corpus gate
  holds MetaQuotes' Standard Library and examples at 0 undeclared-name and 0 parse errors.
- Prefer adding or enhancing over removing. The AI Code Healing subsystem stays removed.
- When the plugin can't know something (an unreadable process table, an unresolved name), it says so
  or takes the safe side; it doesn't guess.

### II. Sturdy platform API (NON-NEGOTIABLE)
- Every platform API used exists, un-deprecated, on both 2025.3.2 (since-build) and the newest verified
  IDE (CLion 2026.3). javac runs with `-Werror` on deprecation and removal.
- No `@ApiStatus.Internal` or experimental API, even for a wanted feature (the owner declined the
  `search_symbol` hook on 2026-11-15 for this reason). Use `hints.declarative`, not `codeInsight.hints`.
- The Plugin Verifier reports stay Compatible with no experimental or internal API. The only allowed
  deprecated usage is an override the oldest platform still declares abstract, with an explained
  `@SuppressWarnings("deprecation")`.
- Respect the threading model: read actions for PSI and indexes, long work off the EDT,
  `getActionUpdateThread()`, dumb-mode guards, and `ProcessCanceledException` always propagates.

### III. No MetaQuotes text or code in the repo (NON-NEGOTIABLE)
- No documentation text from mql5.com and no MetaQuotes code is copied into this repository.
- Catalog files hold API names only, each verified by compiling in MetaEditor.
- The corpus gate reads the Standard Library from the local MetaTrader install; it never copies it.

### IV. Read-only toward MetaTrader
- The plugin never kills MetaTrader and never writes into the MetaTrader trees. The only exception is
  the user-run backtest, which goes through `mt5 backtest --no-kill`.
- A backtest is refused while `terminal64`, `metatester64` or an `mt5 backtest` driver runs, and while
  the process table can't be read. Background compiles skip while a tester runs.
- During development, nothing is compiled in MetaEditor and no heavy MT5 work runs next to a running
  backtest (check `ps -axww -o command=` first).

### V. Every gate stays green
A change is done only when all of these pass:
- `./gradlew build` (compile with `-Werror`, plus every unit test; currently 643);
- `./gradlew verifyPlugin verifyPluginStructure` before a release;
- the corpus gate does not get worse than `src/test/resources/gate/corpus-baseline.properties`
  (a deliberate change commits the new baseline with it);
- after an install, the live check `tools/clion-mcp-check.py ... --expect N` matches the last known count.

Tests are hermetic: they never depend on this machine's MetaTrader install.

## Repository Constraints
- Source is Java 21, not Kotlin. Every extension is registered in `plugin.xml`, and removing one removes
  its registration. The stub schema version is bumped whenever stub structure changes.
- A release bumps `version` in `build.gradle.kts` and `<version>` in `plugin.xml` together.
- The plugin is installed into CLion only when the owner asks. Installing restarts CLion, which other
  sessions use. Install over the top with a backup; never uninstall. Quit CLion with osascript, never
  force-kill it.
- `.specify/` keeps Spec Kit's fixed layout. Feature specs live in `specs/<NNN-feature>/`.
- `docs/` is gitignored in this repo, so Spec Kit usage notes live in `CLAUDE.md`.

## Development Workflow
1. **New features** go through `/speckit-specify`, then `/speckit-clarify` (optional), `/speckit-plan`,
   `/speckit-tasks`, `/speckit-analyze` (optional), `/speckit-implement`, and `/speckit-converge`.
   Fixes and small changes keep the direct path: edit, `./gradlew build`, commit.
2. A plan names the platform APIs it will use and confirms each against Principle II before any code.
3. **Commits and merges:**
   - commits stage paths explicitly and end with the attribution trailer;
   - no push, no PR and no merge to `master` without the owner's go;
   - branches are made by hand (Spec Kit's git extension is not installed).

## Governance
- This constitution summarises the rules in `CLAUDE.md` and does not override them. If the two
  disagree, `CLAUDE.md` wins, and this file is corrected.
- **Amendments:**
  - only on the owner's instruction, through `/speckit-constitution`, with an updated Sync Impact Report;
  - version bumps follow semantic versioning: MAJOR when a principle is removed or redefined, MINOR when
    one is added, PATCH for wording.
- **Compliance:** `/speckit-plan`'s Constitution Check and `/speckit-analyze` check every plan against
  Principles I–V.

**Version**: 1.0.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-17
