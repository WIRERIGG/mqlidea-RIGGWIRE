# Implementation Plan: Template Type Parameters Resolve

**Branch**: `002-template-parameters` | **Spec**: [spec.md](spec.md) | **Pre-mortem**: [premortem.md](premortem.md)

## Approach

- **Parser** (`TopLevelParsing.parseTemplateHeader`, also called from `ClassParsing.parseClassInnerBlock` for member templates): `template < (typename|class) NAME {, (typename|class) NAME} >` becomes a `TEMPLATE_HEADER` holding one `TEMPLATE_PARAMETER` per name. Anything else (incomplete while typing, non-type parameters) rolls back and stays loose tokens exactly as before. The declaration after the header parses unchanged, so the risk to existing parses is limited to the header tokens.
- **PSI**: `MQL4TemplateParameterElement` (plain PSI, no stub: file-local by definition, so the stub version stays 27). `PsiNameIdentifierOwner`, use scope = its file.
- **Resolve** (`MqlResolveUtil.resolveTemplateParameter`): walking up from a use, any ancestor whose previous sibling is a `TEMPLATE_HEADER` offers that header's parameters, innermost first. Runs after `::` and `offsetof` handling, before locals and globals (FR-003), and never after a `.`.
- **Declaration names**: `MqlPsiUtil.isDeclarationNameIdentifier` knows the parameter's name, so it isn't a reference.
- **Find usages / rename**: type "template parameter"; in-place rename enabled.
- **Undeclared checks (US3)**: the name-anywhere fallback in `UndeclaredNames.collectOutsidePsi` and its helpers are removed.

## Constitution check

I honest diagnostics: a stray `T` is reported again (as MetaEditor does), measured by the corpus gate at 0 false errors. II platform API: only `PsiTreeUtil`, `LocalSearchScope`, `PsiNameIdentifierOwner`. III no MetaQuotes code: tests use hand-written snippets. IV read-only toward MetaTrader: no change. V gates: build, corpus gate, public corpus as a report corpus.
