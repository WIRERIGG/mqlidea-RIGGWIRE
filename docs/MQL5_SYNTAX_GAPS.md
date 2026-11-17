# MQL5 syntax gaps: plugin vs. the MQL5 language reference

Audit of the plugin's lexer, parser, PSI, resolver and default-on inspections against the MQL5
language reference (`docs/basis`, the bundled copy in `src/main/resources/mql/doc/en/basis` plus the
live pages on mql5.com where the bundled copy is older).

**Method.** Each snippet below is valid MQL5: it compiles with **0 errors** (warnings noted where relevant) in the real
MetaEditor (build on this machine, via `mt5 compile`, under `MQL5/Scripts/zprobe/`). It is then parsed
by the plugin with every default-on inspection enabled (`src/test/java/probe/SyntaxProbeTest.java`,
run with `MQL_PROBE_DIR=<dir> ./gradlew test --rerun --tests probe.SyntaxProbeTest`). From iteration 3 the
probe also reports every use of a name declared in the same file that does not resolve (`UNRESOLVED`;
built-ins are not checked). A gap is
recorded only when the compiler accepts the code and the plugin rejects it, mis-flags it, or builds
the wrong PSI for it.

**Severity.**
- **High**: a false error (these also switch off the MetaEditor annotator for the whole file, because
  `MqlCompilerExternalAnnotator` skips files with parse errors), *or* a resolve gap on very common
  code where rename silently produces code that no longer compiles (F-1, V-1, P-1, OOP-1).
- **Medium**: wrong or missing PSI, so navigation, the structure view, resolution and the inspections
  silently miss code.
- **Low**: highlighting or completion only.

## Coverage

| Area (docs/basis) | Status |
|---|---|
| Syntax: comments, identifiers, reserved words | done (iteration 1) |
| Data types | done (iteration 2) |
| Operations and expressions | done (iteration 3) |
| Operators | done (iteration 4) |
| Functions | done (iteration 5) |
| Variables | done (iteration 6) |
| Preprocessor | done (iteration 7) |
| Object-oriented programming | done (iteration 8) |
| Namespaces (live docs only, not in the bundled copy) | done (iterations 1 and 9) |

---

## Syntax (comments, identifiers, reserved words)

The live reserved-words page lists four words that the lexer has no token for: `union`, `pack`,
`offsetof` and `group`. All four are lexed as `IDENTIFIER`. Comments, 63-character identifiers,
leading-underscore identifiers, `override`/`final`, `#ifdef`/`#ifndef`/`#else`/`#endif`, `template`,
`typename` and `dynamic_cast` all parse with no gaps.

### S-1 (High): `pack(n)` on a struct is a parse error

```mql5
struct Packed pack(4)
  {
   char c;
   int  i;
  };
void OnStart() { Print(sizeof(Packed)); }
```

MetaEditor: 0 errors. Plugin: `Unexpected token` (ERROR) at ` pack(4)`. Because the file now has a
parse error, the compiler annotator also stops running on it.
**Fix:** add a `PACK_KEYWORD` token and accept an optional `pack ( <const-expr> )` after the struct
name in `ClassParsing`.

### S-2 (Medium): `union` is not a type

```mql5
union LongDouble
  {
   long   long_value;
   double double_value;
  };
void OnStart() { LongDouble lb; lb.double_value=1.5; Print(lb.long_value); }
```

MetaEditor: 0 errors. Plugin: no error, but `union` and `LongDouble` are two bare `IDENTIFIER`s
followed by a loose `BRACKETS_BLOCK`. There's no `MQL4ClassElement`, so a union gets no structure-view
entry, no stub index entry, no Go to Class, and no member resolution or rename for
`lb.double_value`. Highlighting doesn't treat `union` as a keyword.
**Fix:** add `UNION_KEYWORD` to the lexer and parse it like `struct` in `ClassParsing`, so it becomes a
class element and enters the class stub index. Bump `STUB_SCHEMA_VERSION` if the stub gains a kind.

### S-3 (Medium): `namespace` bodies are not parsed

```mql5
namespace Utils
  {
   int Twice(int x) { return x*2; }
  }
void OnStart() { Print(Utils::Twice(3)); }
```

MetaEditor: 0 errors. Plugin: `namespace` is lexed (`NAMESPACE_KEYWORD`), but the body is a generic
`BRACKETS_BLOCK`. `int Twice(int x)` becomes an `EXPRESSION_STATEMENT` plus loose blocks, not a
function element. So every function, class and enum inside a namespace is invisible to the structure
view, Go to Symbol, the stub indexes and resolution. `Utils::Twice` doesn't navigate, and the
function-level inspections (return checks, handle leaks, etc.) never see code inside a namespace.
**Fix:** parse `namespace Name { ... }` as a container whose body runs the same top-level loop as
`MQL4Parser.doParse` (functions, classes, enums, globals, nested namespaces). Then resolve
`Name::member` through it.

### S-4 (Low): `input group "..."` is not a declaration

```mql5
input group "Signal"
input int    InpPeriod=14;
sinput string InpNote="x";
void OnStart() { Print(InpPeriod); }
```

MetaEditor: 0 errors. Plugin: no error, but `group` is an `IDENTIFIER` and `input group "Signal"` is a
loose `INPUT_KEYWORD IDENTIFIER STRING_LITERAL` run at file level. It isn't highlighted as a keyword,
isn't folded, and isn't shown as an inputs section in the structure view. Harmless today because
input-related inspections key on `VAR_DECLARATION_STATEMENT`.
**Fix:** add `GROUP_KEYWORD` and parse `input group <string>` as its own element (it is not a
variable).

### S-5 (Low): `offsetof` is not a keyword

```mql5
struct S { char c; int i; };
void OnStart() { Print(offsetof(S,i)); }
```

MetaEditor: 0 errors. Plugin: parses as a call to an unknown function `offsetof`. There's no error,
but it isn't highlighted as a keyword, and `S`/`i` aren't resolved as type and member.
**Fix:** add `OFFSETOF_KEYWORD` and treat it like `sizeof`.

### Inspection false positives seen in this area (default-on)

- **I-1 (Medium) `MissingInputValidation` on scripts.** It reports "File has input parameters but no
  OnInit() to validate them" on a script, whose entry point is `OnStart()`, and a script has no
  `OnInit()` to add. It should accept validation in `OnStart()`, or skip files whose only entry point
  is `OnStart`.
- **I-2 (Low) `NullAfterDelete` on locals going out of scope.** It reports `'delete a' without
  subsequent 'a = NULL'` when `delete a;` is the last statement of the block that declares `a`. The
  pointer can't dangle there because the variable dies with the block. It should skip locals whose
  declaring block ends right after the `delete`.

---

## Data types

All 12 type snippets compile with 0 errors and 0 warnings in MetaEditor. Integer, hex and `ulong`-max
literals, `C'r,g,b'` and `clrXxx` colors, enums, fixed, initialized and dynamic arrays, pointers and
`&` references, casts, `dynamic_cast`, structs with constructors, struct inheritance, `{...}` struct
initializers, adjacent string-literal concatenation, `this`, and template classes all parse with no
false errors. Every gap here is in the **lexer**. The parser tolerates the broken tokens, so no
`PsiErrorElement` appears and the compiler annotator keeps running. The damage is false
bad-character highlighting (`HighlighterColors.BAD_CHARACTER`, which renders like an error) plus
garbage tokens that the inspections and resolution then see.

Probe note: the plugin uses its own `MQL4Elements.BAD_CHARACTER`, not `TokenType.BAD_CHARACTER`, so
the first version of the probe under-reported these. The probe now matches both. Rerun on every
snippet so far, it finds bad characters only on the three literal lines of the T-1/T-2 snippet; the
iteration 1 snippets have none.

### T-1 (High): datetime literals `D'...'` are not lexed (FIXED on branch `fix/lexer-datetime-hex-literals`)

```mql5
void OnStart()
  {
   datetime d1=D'2024.01.15 12:30:00';
   datetime d2=D'19.07.1980 12:30:27';
   datetime d3=D'19.07.1980 12';
   datetime ny=D'2015.01.01 00:00';
   Print(d1,d2,d3,ny);
  }
```

MetaEditor: 0 errors. Plugin: there's no lexer rule for it, so `D'2024.01.15 12:30:00'` becomes
`IDENTIFIER(D)`, `BAD_CHARACTER(')`, `DOUBLE(2024.01)`, `DOUBLE(.15)`, `INT(12)`, `INT(30)`, `INT(0)`,
`INT(0)`, `BAD_CHARACTER(')`. Each quote is painted as a bad character. Time filters in EAs use this
literal constantly. `color_string_literal` already shows the pattern for the fix.
**Fix:** add `datetime_literal = D \' [0-9.: ]* \'` returning a new `DATETIME_LITERAL` (highlight it as
a number or string, and accept it wherever `COLOR_STRING_LITERAL` is accepted as a constant).

### T-2 (High): `\xHH` escapes break char and string literals (FIXED on branch `fix/lexer-datetime-hex-literals`, along with the documented `\d` decimal codes)

```mql5
void OnStart()
  {
   char   c='\x41';
   string copy="Copyright\t\x00A9";
   Print(c,copy);
  }
```

MetaEditor: 0 errors. This is the documented form: the *Character Constants* page uses `'\x10'` and
the *String Type* page uses `"\x00A9"`. Plugin: `escape_sequence_spec_char` has no `\x` alternative,
so `'\x41'` becomes `BAD_CHARACTER IDENTIFIER(x41) BAD_CHARACTER`. In the string case **both
double quotes** become bad characters and the string's contents are tokenized as code. The
inspections and the problems log then see identifiers that don't exist.
**Fix:** add `"\\x" [0-9a-fA-F]+` (the docs allow up to 4 hex digits) to `escape_sequence`.

### T-3 (Low): trailing-dot floats `5.` lex as an integer and a dot

```mql5
void OnStart() { double t=5.; Print(t); }
```

MetaEditor: 0 errors. Plugin: `INTEGER_LITERAL(5)` followed by `DOT`, because `decimal_float_simple`
requires digits after the dot. Nothing visible breaks today, but the type is wrong and the stray
`DOT` looks like member access to the resolver.
**Fix:** allow `[0-9]+ \.` (not followed by an identifier character) as a double.

### T-4 (Medium): `typedef` function-pointer types are not declarations

```mql5
typedef int (*TBinaryOp)(int,int);
int Add(int a,int b) { return a+b; }
int Apply(TBinaryOp op,int a,int b) { return op(a,b); }
void OnStart() { TBinaryOp f=Add; Print(f(1,2)," ",Apply(Add,5,3)); }
```

MetaEditor: 0 errors. Plugin: `typedef` is an `IDENTIFIER` (no keyword), and the line is
`IDENTIFIER INT_KEYWORD BRACKETS_BLOCK BRACKETS_BLOCK ;` at file level. `TBinaryOp` is not a named
element, so Go to Declaration, Find Usages and rename don't work on it, the structure view leaves it
out, and `TBinaryOp f=Add;` is not a variable declaration.
**Fix:** add `TYPEDEF_KEYWORD` and parse `typedef <ret> (*Name)(<params>);` as a named, stub-indexed
type alias.

### T-5 (Low to Medium): `vector`/`matrix`/`complex` types have no support

```mql5
void OnStart()
  {
   vector  v={1,2,3};
   vectorf vf={1,2};
   matrix  m={{1,2},{3,4}};
   complex z={1,2};
   Print(v.Sum()," ",m.Transpose()[0][1]," ",z.real," ",vf.Size());
  }
```

MetaEditor: 0 errors. Plugin: no errors, but `vector`, `vectorf`, `matrix`, `matrixf`, `vectorc` and
`complex` are plain identifiers. They aren't highlighted as types, the declarations are not
`VAR_DECLARATION_STATEMENT`s (so `v`/`m` don't resolve), and there's no completion or quick doc for
the ~150 matrix/vector methods. The bundled doc tree (`mql/doc/en`) has no *Matrix and Vector Methods*
section at all (live: mql5.com/en/docs/matrix).
**Fix:** treat these names as built-in type keywords in the parser's type gate, and import the
matrix/vector doc section into the bundled catalog to get completion and quick docs.

(An earlier draft listed a T-6 about the `clr*` color list. It was wrong: the list in `MQL4Lexer.flex`
is complete, and `MqlColorAwareLexer` already turns bare names like `Gold` back into identifiers.)

---

## Operations and expressions

All 8 snippets compile with 0 errors in MetaEditor (`o07`, the deliberately unparenthesized precedence
mix, gets 2 compiler warnings, as expected). The plugin raises **no** false errors or default-on
inspection warnings in this area. That covers arithmetic, pre/post `++`/`--`, all 10 compound
assignments, chained `y=z=x`, comparison and logical operators, `!(...)`, bitwise `~ & | ^ << >>`,
indexing including nested `arr[arr[0]-1]`, the comma operator in `for(i=0,j=10;...;i++,j--)`, nested
ternaries, casts, `sizeof`, `Class::Static()` and global-scope `::Print()`. `CMath::Square` and
comma-separated declarations (`int sum=a+b, diff=a-b, ...`) resolve.

Design note: expressions are not parsed into an expression tree. Statement children are a flat
token run, so operator precedence (the docs' *Precedence Rules* table) isn't modeled anywhere. That's
harmless for the current features, but it's why the next item can't be fixed locally.

### O-1 (Medium): members reached through an indexed element or a call result don't resolve

```mql5
struct SBar { double high; double low; };
class CCounter
  {
   int m_n;
public:
   CCounter *Inc(void) { m_n++; return GetPointer(this); }
  };
void OnStart()
  {
   SBar bars[2];
   bars[0].high=1.5;                     // 'high' unresolved
   double range=bars[0].high-bars[1].low; // 'high', 'low' unresolved
   CCounter c;
   c.Inc().Inc();                        // second 'Inc' unresolved
  }
```

MetaEditor: 0 errors. These are the documented *Other Operations* forms: indexing followed by
structure-element access. Plugin: the probe reports `UNRESOLVED` for every `bars[i].field` and for a
member called on a call result. Go to Declaration, Find Usages and rename all miss these uses, so
**renaming `SBar.high` silently leaves `bars[0].high` stale**, and the code no longer compiles.
`CLAUDE.md` lists array-element and return types as out of scope for `MqlTypeResolver`, but the
rename consequence makes this more than a navigation nicety. Arrays of structs (`MqlRates rates[]`,
`MqlTick ticks[]`, user `SBar bars[]`) are among the most common MQL patterns.
**Fix:** in `MqlTypeResolver`, handle a qualifier ending in `]`: strip the index blocks and use the
array variable's declared element type. For `f().m`, read the resolved function's return type from
the tokens before its name. The function stub doesn't store it: it holds only name, signature and
declaration flag. `MQL5SafetyInspectionBase.getReturnTypeNode` reads built-in return types this way,
but a class return type like `CCounter *` is an `IDENTIFIER`, which it doesn't handle yet. Until then, rename should at least warn when
unresolved same-named members exist in the include closure.

The same probe pass also confirms S-2 (`lb.double_value` on a `union` doesn't resolve) and S-5
(`offsetof(S,i)` doesn't resolve `i`). It also shows that members of template instances
(`CStack<int> s; s.Push(1)`) don't resolve. That one is filed under OOP/templates, iteration 8.

---

## Operators (statements)

All 7 statement snippets compile with 0 errors in MetaEditor. The parser handles every form in the
reference with no parse errors and no unresolved names: `if`/`else if`/`else` with and without braces,
`switch` with stacked `case` labels, a char `case 'A':`, fall-through, `{}` blocks inside a `case` and a
one-case switch, `while(true)`/`for(;;)` with `break`, `do ... while`, `for` with a declaration and a
comma list, `continue`, nested loops, `new`/`delete` on pointer-array elements, `return(x)`, `return x`,
bare `return;`, nested compound blocks, and empty statements.

The inspection results agree with MetaEditor in one case. `SuspiciousSemicolon` on `if(x>0) ;`
matches the compiler's own `warning 69: empty controlled statement found`, so that's a true positive.
The rest are below.

### I-3 (High, false negatives): most inspections never look inside class-body methods or namespaces

```mql5
class CLoader
  {
public:
   void Load(void)                                      // method defined in the class body
     {
      MqlRates rates[];
      CopyRates(_Symbol,PERIOD_CURRENT,0,10,rates);      // unchecked: NOT reported
      int h=iMA(_Symbol,PERIOD_CURRENT,14,0,MODE_SMA,PRICE_CLOSE); // unchecked: NOT reported
      Print(rates[0].close,h);
     }
  };
void OnStart() { CLoader l; l.Load(); }
```

MetaEditor: compiles. Plugin: **no** `UncheckedCopyRates`, `UncheckedHandle` or
`MissingIndicatorRelease`. The identical body as a top-level function, or as an out-of-line
`void CLoader::Load(void) { ... }`, gets all three warnings. The same code inside
`namespace Data { void Load() { ... } }` also gets nothing, because namespace bodies aren't parsed
(S-3).

Cause: 68 of the 80 inspections (by text search) find functions by scanning only
`file.getChildren()`, through `MQL5SafetyInspectionBase.findFunctions` or their own loop over the
file's children. An in-class method is a function element nested inside `CLASS_INNER_BLOCK`, so it's
never visited. In this repo's own EA tree the exposure is small (6 of 147
`CopyBuffer`/`CopyRates`/`iMA`/`iATR`/`iCustom`/`OrderSend` calls sit inside class bodies). But code
written with methods inside the class body would get no Trading Safety coverage on those methods.
**Fix:** make `findFunctions` (and the loops that duplicate it) walk every `MQL4FunctionElement` in
the file, e.g. via `PsiTreeUtil.findChildrenOfType`, or descend into `MQL4ClassElement` inner blocks
and (after S-3) namespace bodies. One shared helper fixes all 68. Add a regression test that runs the
Trading Safety group on an in-class method.

### I-4 (Medium): `NewKeywordInLoop` flags the normal way to fill a pointer array or container

```mql5
class CItem { public: int v; CItem(int x) : v(x) {} };
void OnStart()
  {
   CItem *items[3];
   for(int i=0; i<3; i++)
      items[i]=new CItem(i);          // WARNING: "potential memory leaks"
   for(int i=0; i<3; i++)
     {
      delete items[i];
      items[i]=NULL;
     }
  }
```

MetaEditor: 0 errors, 0 warnings. Plugin: a default-on WARNING, "Heap allocation ('new') inside
loop ... potential memory leaks". The inspection flags *any* `NEW_KEYWORD` in a loop body. Storing
each object in a distinct slot (`items[i]=new ...`) or handing it to a container
(`list.Add(new CItem(i))`, the Standard Library's `CArrayObj` pattern) is how MQL5 builds collections.
That's neither a leak nor avoidable overhead.
**Fix:** report only when the `new` result is assigned to a plain local (not an indexed element, a
member, or a call argument) that's reassigned on the next iteration without a `delete`. Or keep the
current rule but lower it to WEAK WARNING and reword it as a performance hint.

### I-5 (Low): `SuspiciousSemicolon` on an intentional empty `for` body

```mql5
void OnStart() { int k=0; for(k=0; k<3; k++); Print(k); }
```

MetaEditor: no warning for the `for` form. It warns only for `if(...) ;` (see above). Plugin:
WARNING. The empty-body `for` that only advances its counter is a recognized idiom, so this is a
judgment call. Consider skipping `for` statements whose third clause has a side effect, or offering
the usual "replace `;` with `{}`" quick-fix so the intent can be made explicit.

---

## Functions

All 8 function snippets compile with 0 errors in MetaEditor. No problems with: by-value, `&`
by-reference, `const &` struct and `const double &a[]` array parameters, default arguments, overloads
by parameter type, a prototype followed by a later definition, recursion, `static` locals, every EA
event handler (`OnInit` returning `ENUM_INIT_RETCODE`, `OnDeinit(const int)`, `OnTick`, `OnTimer`,
`OnTrade`, `OnTradeTransaction`, `OnChartEvent`, `OnBookEvent`, `OnTester`, `OnTesterInit/Deinit`),
both `OnCalculate` forms, and `#import "x.dll"` / `#import "x.ex5"` blocks. All parameter kinds
resolve.

### F-1 (High): most variable declarations are not declarations (locals, globals and class fields) (FIXED on branch `fix/declaration-parsing`)

```mql5
class CItem { public: int v; };
class CEngine
  {
public:
   CItem            *m_ptr;       // pointer field:  not a member
   double            m_buf[];     // array field:    not a member
   int               m_count;     // scalar field:   OK
  };
CItem  g_obj;                     // class-typed global: unresolved
int    g_arr[5];                  // array global:       unresolved
double g_init[]={1.0,2.0};        // initialized array:  unresolved
void OnStart()
  {
   CItem cfg;                     // class/struct local: unresolved
   CItem *ptr=NULL;               // pointer local:      unresolved
   int fixed[3];                  // fixed array local:  unresolved
   int i,j;                       // comma list, no '=': both unresolved
   double plain=1.0;              // scalar with '=':    OK
   CEngine e;
   e.m_count=1; ArrayResize(e.m_buf,3); e.m_ptr=NULL;
  }
```

MetaEditor: 0 errors (checked with the `r01`/`r02`/`r04` probe files, which contain exactly these
declarations). Plugin: a targeted resolve probe (`src/test/java/probe/ResolveProbeTest.java`) reports
every commented declaration above as **UNRESOLVED**, including `e.m_buf` and `e.m_ptr`. Only built-in
scalar declarations of the form `type name;` or `type name = ...` and parameters resolve.

Cause: `StatementParsing.parseLocalVarDeclaration` (line 214) is used for function bodies, the top
level (`MQL4Parser`) and class bodies (`ClassParsing`). It accepts a declaration only when it is
`[const|static|input|...] <built-in type keyword> IDENTIFIER` followed by `;` or `=`. So it rejects a
user type (`IDENTIFIER IDENTIFIER`), a pointer (`*`), an array (`[`) and a comma list without an
initializer (`int i,j;`). Those fall through to `EXPRESSION_STATEMENT`, with no `VAR_DEFINITION`, no
global-variable stub, and no member entry. This is why the probe found `SCfg cfg;` unresolved in
`f01`, `int n[]={1,2,3};` unresolved in `f02`, and `SBar bars[2]` not resolving in O-1.

Impact: Go to Declaration, Find Usages, rename, highlighting usages, the structure view and dot
completion don't work on any of these. That includes the most common declarations in EA code:
`CTrade trade;`, `CPositionInfo pos;`, indicator buffers `double buf[];`, `int handles[];`,
`MqlRates rates[];` and pointer members. The 8 inspections that key on `VAR_DECLARATION_STATEMENT` or
`VAR_DEFINITION` (uninitialized and unused variables, input validation, naming, globals count, etc.)
also don't see them. **This is the single largest PSI gap found so far.** It's also why O-1 and the
member half of S-2 can't be fixed in the type resolver alone.
**Fix:** widen the gate to accept `IDENTIFIER IDENTIFIER`, an optional `*` or `&` before the name,
`[...]` array suffixes after it, and `,`-separated names, keeping it narrow enough not to swallow
calls (`Foo(bar);`) or expressions (`a*b;`). For example, require that the token after the name (and
its `[...]` groups) is `;`, `=`, `,` or `(` for constructor arguments. `parseVarDefinitionList` then
needs to consume `[...]` groups and `{...}` initializers. Bump `STUB_SCHEMA_VERSION`, since many more
globals will be stubbed.

### F-2 (High): the `export` modifier is a parse error

```mql5
#property library
int Twice(int v) export { return v*2; }
```

MetaEditor: 0 errors (*Exporting Functions* page). Plugin: `Function body or semicolon expected`
(ERROR) on each exported function. As with S-1, the parse error also turns off the compiler annotator
for the whole library file. `v` inside the body is also left unresolved.
**Fix:** add `EXPORT_KEYWORD` to the lexer and accept it between `)` (and `const`) and the body in
`FunctionsParsing`.

### F-3 (Low to Medium): `StackOverflowRisk` on recursion that has a base case

```mql5
int Fact(int n) { if(n<=1) return 1; return n*Fact(n-1); }
```

Plugin: WARNING "appears to call itself recursively without depth limit", even though the first
statement is a guarded `return`. **Fix:** skip functions whose body has a `return` under an `if`
before the recursive call, or lower the warning to a weak hint.

### F-4 (Low): `EmptyEventHandler` is a WARNING

Five empty handlers in the EA snippet (`OnTick`, `OnTimer`, `OnTrade`, `OnTesterInit`,
`OnTesterDeinit`) each get a default-on WARNING. Empty handlers are harmless. `OnTesterInit` and
`OnTesterDeinit` are sometimes declared empty on purpose, because their presence switches the tester
into frame mode. A WEAK WARNING fits better.

### D-1 (Medium): the bundled language reference is the MQL4 one

`src/main/resources/mql/doc/en/basis` mentions MQL4 66 times and MQL5 7 times. Its pages describe
MQL4 behavior (*"The MQL4 language provides..."*, `#property strict`, a *"Record in MQL4"* column). Its
event-handler page has no `OnTradeTransaction` or `OnBookEvent`, and the tree has no namespace,
union, `vector`/`matrix` or conditional-compilation material. Quick documentation for MQL5 language
constructs therefore shows MQL4 text. **Fix:** refresh `mql/doc/en/basis` (and `ru/basis`) from the
MQL5 reference, or serve dialect-specific trees via `MqlDialect`.

---

## Variables

The 4 valid snippets compile with 0 errors in MetaEditor and parse with no parse errors or bad
characters: `input group`, `input`/`sinput` with trailing description comments, enum and
`ENUM_TIMEFRAMES` inputs, `static` globals and locals, `const` globals and locals, `{...}` initializer
lists for structs and 2-D arrays, `1e-5` and `.5` literals, nested-block shadowing, and two
consecutive `for(int i...)` loops. Scalar inputs, static locals and the innermost shadowed `value`
all resolve to the right declaration. `InpMode` and `InpTf` (enum-typed inputs) don't resolve; that's
F-1 again (a non-keyword type).

### V-1 (High): `for` loop counters never resolve (FIXED on branch `fix/declaration-parsing`)

```mql5
void OnStart()
  {
   for(int i=0; i<2; i++)
     {
      Print(i);            // UNRESOLVED
     }
  }
```

MetaEditor: compiles. Plugin: `i` inside the body doesn't resolve, with or without braces, and with
one loop or two. So there is no Go to Declaration, highlight usages or rename for the most common
local in any MQL program, and the counter rename refactoring doesn't work. The for-init clause is
parsed by `parseEmbeddedVarDeclarationOrAssignmentOrFail`. That path makes no `VAR_DEFINITION` the
resolver's local walk can find, unlike `parseLocalVarDeclaration`. Exposure: the RIGGWIRE EA tree
has 296 `for(int ...)`-style loops.
**Fix:** have the for-init section emit a `VAR_DEFINITION` per declared name (sharing the F-1 widened
definition-list parser), and teach `MqlResolveUtil`'s local walk that a `for` statement's init
definitions are in scope for its condition, increment and body.

### V-2 (Medium): `::name` resolves to the shadowing local, not the global

```mql5
int value=1;
void OnStart()
  {
   int value=2;
   Print(::value);         // resolves to line 4 (the local); should be line 1
  }
```

MetaEditor: compiles, and `::value` is the global (*Visibility Scope* page, global scope resolution
operator). Plugin: Go to Declaration on `::value` jumps to the local `value`. Rename of the global
misses this use, and rename of the local wrongly changes it. Exposure is low (the RIGGWIRE tree has no `::name` variable uses). **Fix:** when the reference is
preceded by a bare `COLON_COLON` (no qualifier identifier before it), skip locals, parameters and
class members and search the file/include-closure globals only.

### V-3 (Low): MQL5 `extern` initialization isn't flagged

```mql5
extern int g_ext=3;
```

MetaEditor (MQL5): `error 303: extern variable initialization is not allowed`. Plugin: nothing until
the compiler annotator runs (and only once the file is otherwise error-free). This is legal in MQL4,
so the check must be dialect-aware (`MqlDialect`). A small MQL5-only inspection, or an annotator
error, would catch it early, which matches the project rule of detecting errors inline.

### V-4 (observation): `PrintInOnTick` on a single `Print`

`void OnTick() { Print(InpPeriod); }` gets a WARNING for excessive logging. That's a reasonable
default-on hint for EAs, so it isn't recorded as a gap. It's here only so a later audit doesn't
re-flag it.

---

## Preprocessor

All 6 snippets compile with 0 errors in MetaEditor once the resource paths point at real files.
`#property icon` and a `#resource ... as string` text file failed only for file and path reasons, not
syntax; `#resource ... as bitmap g_pixels[][]` compiles. The parser accepts, with no parse errors:
constant and function-like `#define`, multi-line `\` continuations, `#undef`, `#ifdef`/`#ifndef`/
`#else`/`#endif` at the top level, in class bodies, in constructor bodies and *inside a call's
argument list*, predefined macros (`__MQL5__`, `__MQL5BUILD__`, `__FILE__`, `__LINE__`,
`__FUNCTION__`, `__DATETIME__`, `__PATH__`), every `#property` form tried, `#include <...>` and
`"..."`, and `#resource`. A class member declared under `#ifdef` (`b.h`) still resolves.

### P-1 (High): macros are invisible to navigation, find usages, rename and completion

```mql5
#define MAX_BARS 500
#define SQR(x)   ((x)*(x))
void OnStart()
  {
   int a=SQR(3)+MAX_BARS;   // both UNRESOLVED
  }
```

MetaEditor: compiles. Plugin: `MAX_BARS` and `SQR` (and `TRACE` defined under `#ifdef`, and the
`DEBUG_MODE` flag tested by `#ifdef`) have no reference target. The PSI has no named element for a
macro: `PREPROCESSOR_DEFINE_BLOCK` is produced only by `PreprocessorIfDefParsing`, and nothing in
`reference/`, `index/`, `editor/` (completion) or `structure/` mentions macros. So Go to Declaration,
Find Usages, rename, completion and Go to Symbol don't work for any `#define`, and the structure view
doesn't list them. The RIGGWIRE EA tree has **209** `#define` lines (magic numbers, buffer indexes,
feature flags), so this is a large everyday navigation gap.
**Fix:** make the `#define` name an `MQL4DefineElement` (`PsiNameIdentifierOwner`, stubbed into a new
`MqlDefineIndex`, which needs a `STUB_SCHEMA_VERSION` bump). Add it as a resolve target after locals
and globals in `MqlResolveUtil` (file, then include closure, then index). Make identifiers inside
`#ifdef`/`#ifndef`/`#undef` references too, and add define names to completion. Expansion isn't
needed for navigation.

### P-2 (Medium): stringize `#` and token-paste `##` in macro bodies lex as BAD_CHARACTER

```mql5
#define STR(x)   #x
#define CAT(a,b) a##b
void OnStart() { int CAT(var,1)=1; Print(STR(hello)," ",var1); }
```

MetaEditor: compiles (`#` and `##` are documented on the *Macro substitution* page). Plugin: three
BAD_CHARACTER tokens on lines 7 and 8. These show as error-highlighted characters and break
highlighting and brace matching for the rest of the macro line. 6 of the RIGGWIRE macro bodies use
one of these operators. **Fix:** in `MQL4Lexer.flex`, inside the define-body state, lex `##` and a
`#` before an identifier as operator tokens (e.g. `PP_STRINGIZE`/`PP_CONCAT`), then regenerate the
lexer (recipe in the lexer-fix notes).

(Seen again: I-1 `MissingInputValidation` fires on a *script* with `#property script_show_inputs`.
Scripts have no `OnInit` by design.)

---

## OOP (classes, inheritance, virtual, interfaces, operators, templates)

All 7 snippets compile with 0 errors in MetaEditor and parse with no parse errors or bad
characters. Covered: `protected`/`private`/`public` sections, constructor initializer lists
including the base constructor (`: CShape("circle"), m_r(r)`), virtual destructors, pure virtual
`= 0`, `const` methods, `override`, `final` classes and `override final` methods, `interface` plus
`class X : public IRunner`, `dynamic_cast<CTask*>(r)`, `static` members and methods,
`GetPointer(this)` and `this.m_n`, overloaded `operator+`/`==`/`[]`/`=`, function and class templates
with an explicit `Max<double>(...)` call, out-of-line constructor, destructor and method definitions,
and struct inheritance (`struct SChild : SBase`).

Most UNRESOLVED results in this area are earlier gaps showing up again: `shapes[i].Name()` (array
element, O-1/F-1), `c.Inc()` and `s.Push()` (locals of user or template type, F-1), and
`h.m_child.id` (a user-typed field, F-1). `NullAfterDelete` on `delete r;` as the last statement is
I-2 again. Two gaps are new:

### OOP-1 (High): class fields don't resolve inside out-of-line method bodies, even through `this.`

```mql5
class CEngine
  {
public:
   int               m_state;
   void              Step(int delta);
   void              Inline(void) { m_state++; }   // m_state resolves here
  };
void CEngine::Step(int delta)
  {
   m_state+=delta;      // UNRESOLVED
   this.m_state=1;      // UNRESOLVED
   Inline();            // resolves only via the global-function fallback
  }
```

MetaEditor: compiles. Plugin: inside the out-of-line body, `m_state` and `this.m_state` have no
target, and constructor-initializer uses (`CEngine::CEngine(void) : m_state(0)`) don't either. The
same field resolves inside an in-class body. Cause:
`MqlResolveUtil.resolveEnclosingClassMember` (line 81) looks only for an enclosing
`MQL4ClassElement` whose inner block contains the use. A `Class::Method` definition at the top level
has no such ancestor, and `MqlTypeResolver`'s handling of `this` presumably uses the same lookup.
**Rename hazard:** renaming `m_state` updates the class body and `obj.m_state` but leaves every
out-of-line use stale, so the code no longer compiles. The RIGGWIRE EA tree writes methods inline (2
out-of-line definitions). But the MQL5 Standard Library is written this way (282 out-of-line
definitions in `Include/Trade` alone), and so is the reference documentation's own style.
**Fix:** when no enclosing class body is found, and the enclosing function's name is qualified
(`IDENTIFIER :: IDENTIFIER` before its argument list), resolve the qualifier to its class (file,
include closure, then the class index) and run `resolveMemberInClassHierarchy` on it. Use the same
class for `this` in `MqlTypeResolver`.

### OOP-2 (Medium): out-of-line static member definitions aren't references

```mql5
class CCounter
  {
public:
   static int        s_total;
  };
int CCounter::s_total=0;     // 's_total' UNRESOLVED
```

MetaEditor: compiles. This definition is *required* for a static data member (*Static Members* page).
Plugin: the `s_total` after `CCounter::` resolves to nothing, so renaming the static field leaves this
definition behind and the program fails to link (`'s_total' - undeclared identifier`).
**Fix:** treat `Type Class::name = ...;` at the top level as a qualified member reference, using the
same qualifier-to-class lookup as OOP-1.

Templates: the parser handles the documented forms. Member resolution on template-instance locals
(`CStack<double> s; s.Push(...)`) can't be judged until F-1 is fixed, because `s` itself isn't a
recognized declaration. Re-test after F-1. `T` inside the template body isn't checked.

---

## Namespaces (iteration 9, refines S-3)

Both snippets compile with 0 errors in MetaEditor: nested `Risk::Detail::Helper()`, a class, enum,
const and function inside a namespace, the same function name in two namespaces
(`Risk::Size`/`Signal::Size`), and a namespace reopened in a second block that calls the first
block's function unqualified.

### N-1 (Medium): everything declared in a namespace is missing from the PSI except enum constants

```mql5
namespace Risk
  {
   double Size(double equity) { return equity*0.02; }
   class CGuard { public: bool Ok(double v) { return v<2.0; } };
  }
void OnStart() { Risk::CGuard g; Print(Risk::Size(1000)," ",g.Ok(1.0)); }
```

Plugin: no parse error, but the PSI tree shows the namespace body as a plain `BRACKETS_BLOCK`
*code block*, so `double Size(...) {...}` is an `EXPRESSION_STATEMENT` and not a function element.
`Size`, `Helper`, `CGuard` and `Ok` are all UNRESOLVED. Only the enum constant `Risk::HIGH` resolves,
because enum parsing is reached from statement context. As a result, namespace contents have no
navigation, structure view, Go to Symbol, completion or inspections (all of I-3 applies). Neither
the RIGGWIRE tree nor the terminal's `MQL5/Include` uses `namespace` today, so the impact is Medium,
though it rises for any codebase that adopts namespaces.
**Fix (expands S-3):** in `MQL4Parser`, parse `namespace IDENTIFIER { ... }` as a
`NAMESPACE_BLOCK` whose body runs the *top-level* declaration loop (functions, classes, enums,
globals, nested namespaces). Record the namespace path on function and class stubs so `A::B::F`
resolves qualifier by qualifier, merge reopened blocks of the same name, and let unqualified uses
inside a namespace resolve to its own members first.

---

## Summary (all docs/basis areas covered)

**Status (2026-11-17): every accepted gap is fixed.** The ranked table that stood here was the
fix order during the audit; see "All accepted gaps fixed" below for what each fix does and which
commit carries it (`16d43fc`, `5c8b90b`, `1bab5b1`, `0e19ff0`, `2d95c36`, and `83f5b53` for D-1, which
the owner resolved by showing no MQL4 page in MQL5 files rather than importing mql5.com text).
V-4 was an observation, not a gap.

**Leverage:** F-1, V-1 and OOP-1 all live in the declaration parse gate plus `MqlResolveUtil`'s
scope walk. One focused change to `StatementParsing.parseLocalVarDeclaration`/`parseVarDefinitionList`,
the for-init path, and a qualified-function → class lookup fixes the top two and the seventh, and
unblocks O-1. P-1 is a self-contained new element type and index. I-3 is a one-helper change in
`MQL5SafetyInspectionBase.findFunctions`. Each should land with probe snippets from this file
turned into regression tests.

---

## Corpus baseline (after iteration 9; lexer fix committed as `903c218`)

The audit probe (`SyntaxProbeTest`, now with an `IDENTS n RESOLVED m` line per file) was run over
real code: the 43 RIGGWIRE EA sources and the 8 `Include/Trade` headers. Copies are in the
scratchpad, with each `.mqh` renamed to `.mq5` so the probe picks it up.

| Corpus | Files | PARSE | BADCHAR | Identifiers resolved |
|---|---|---|---|---|
| RIGGWIRE | 43 | 1 | 2 | 23,936 / 50,480 (47.4%) |
| Include/Trade | 8 | 0 | 0 | 1,533 / 3,796 (40.4%) |

The denominator includes built-ins (`Print`, `CopyBuffer`, `ENUM_*` constants), so use the
percentage only for before/after comparison. **Merge gate for F-1/V-1:** PARSE and BADCHAR don't
rise, and the resolved count rises. The older `UNRESOLVED` count is *not* a valid gate, because it
only counts names whose declaration already exists in the PSI. Fixing F-1 adds declarations, so that
count can go *up* while resolution improves.

The 2 BADCHARs are P-2 (`#buffer` stringize in `TrendCipher.mq5`'s `BUFFER_SAFE_SET_DOUBLE`). The 1
PARSE is a new gap:

### T-7 (High): integers with a leading zero lex as two tokens (FIXED in `fix: lex zero-padded decimal integers`)

```mql5
enum ENUM_HOUR
  {
   h00=00,     // 00:00   <- "Unexpected token"
   h07=07,
   h08=08
  };
void OnStart() { Print(h08); }
```

MetaEditor: compiles (`00`, `07` and `08` are accepted as decimal values). Plugin: `decimal_integer =
0 | ([1-9] [0-9]*)` in `MQL4Lexer.flex` lexes `07` as `0` followed by `7`. In an enum this is a
parse error, and the parse error turns off the MetaEditor annotator for the whole file. It's real:
`MQLTA Utils.mqh` has exactly this `ENUM_HOUR`, so that header never gets compile errors inline.
(In a variable initializer such as `int x=08;` the pair is harmless today only because initializers
aren't parsed.) **Fix:** `decimal_integer = [0-9]+`, then regenerate the lexer, and add a
`MqlLiteralLexerTest` case. This is a one-line change.

**Baseline after T-7 (the current gate for F-1/V-1):** RIGGWIRE PARSE 0, BADCHAR 2 (P-2), resolved
23,936 / 50,457. Include/Trade PARSE 0, BADCHAR 0, resolved 1,533 / 3,796.

**Lexer regeneration recipe (verified):** extract the skeleton from the jar
(`unzip jflex-1.7.0-2.jar jflex/idea-flex.skeleton`; the intellij-community copy differs), then run
from the `mql` package dir `java -jar jflex-1.7.0-2.jar --skel jflex/idea-flex.skeleton --nobak -q
-d <out> MQL4Lexer.flex`. Prepend the 6-line copyright header and strip trailing whitespace.

---

## F-1 / V-1 fix (branch `fix/declaration-parsing`)

- **Gate:** `VarDeclarationStatement.declarationNameIndex` accepts
  `modifier* (builtin | Ident(::Ident)*(<args>)?) (*|&)? name ([...])* (; | = | ,)`. Requiring `; = ,`
  *after the array sizes* keeps out calls, prototypes and unterminated lines (`#resource ... as bitmap
  px[][]`, a regression caught by the audit snippets and fixed before commit). `typedef ...;` is
  consumed whole, so its tail isn't taken as a variable.
- **Lists:** `int i,j;` and `int a=1, b, *p;` define every name. A *last* initializer keeps the
  established flat shape after the list. That shape is relied on by `StatementAst`'s raw-initializer
  call handling, which is why every pre-existing inspection result is unchanged.
- **For loops:** `BracketBlockParsing.parseForHeader` parses the init clause as a real declaration.
  `MqlResolveUtil` and local completion treat a `FOR_STATEMENT` header as a scope for its header and
  body (`MqlPsiUtil.forHeaderOf`).
- **Types:** `getDeclaredTypeName` returns the last qualifier segment (`Risk::CGuard` gives `CGuard`)
  and ignores template arguments (`CStack<double>` gives `CStack`), so `s.Push()` on a template
  instance now resolves to the template class's method.
- `STUB_SCHEMA_VERSION` is 24 (more globals are stubbed).
- **Result on the gate:** RIGGWIRE resolved identifiers 23,936 to **32,991** (47.4% to 66.8%) and
  Include/Trade 1,533 to 1,641, with PARSE 0 and BADCHAR unchanged, and the inspection warning set
  identical. The suite has 459 tests (16 new in `reference/MqlDeclarationResolveTest`).
- **Still open, now visible:** member access through an *operator method's* parameter
  (`bool operator==(const CVec &o) const { return x==o.x; }`, where `o.x` is unresolved while
  `o.x` in an ordinary method resolves). It's recorded as **O-2 (Medium)**. Constructor-argument
  declarations `CFoo f(1);` are still not declarations (deliberately excluded, since `T name(` is
  also a prototype).


## Clean pass (2026-11-13, branch `fix/clean-pass`)

Fixed with a regression test each, every snippet checked against MetaEditor:
S-1, F-2, P-2, I-3, I-4, I-1. Also the plugin verifier's 3 CLion 2026.3 compatibility problems
(structure view and `XmlUtil` classes that moved into plugins this one can't see).

Corpus gate after the pass: PARSE 0 and BADCHAR 0 on both corpora (BADCHAR was 2 on RIGGWIRE,
from P-2); resolved identifiers unchanged (32,991 and 1,641). With every inspection on, RIGGWIRE
warnings went 1,428 -> 1,620, almost all from in-class methods now being checked (I-3); spot
checks in NEWS.mqh and RiskManager.mqh are true positives. NewKeywordInLoop 1 -> 0 (I-4).

New findings while verifying:
- `#region` / `#endregion` are not MQL5: MetaEditor reports error 109. The plugin still folds them
  but now marks them as errors.
- `NullAfterDelete` exempts deletes directly in a destructor body (members die with the object);
  without it, I-3 would have flagged nearly every destructor.

Platform API housekeeping (same branch). The plugin verifier went from 21 deprecated, 9
experimental and 1 internal usage on CL 2026.3 to 1 deprecated. That one is
`SdkType.suggestHomePath()`, which is still abstract on 2025.3, and `suggestHomePaths(Project)`
covers for it. Each replacement was checked to exist, un-deprecated, in both IU 2025.3.2 and
CL 2026.3:
- The stub indexes' `get` override became a plain `getElements` method.
- `DaemonCodeAnalyzer.restart(Object)`.
- `getCustomDocumentationElement(..., int)`.
- `ProjectUtil.guessProjectDir`.
- `LazyRunConfigurationProducer`.
- `ComponentWithBrowseButton` with `FileChooser` and the SDK home descriptor.
- `DynamicBundle`.
- The file element type's debug name passed through its constructor.
- `ReadAction.nonBlocking(...).executeSynchronously()` in the problems logger.
- Its own `<tag value=".."/>` helpers in the run configuration. They are parity-tested against the
  deprecated JDOM helpers, so saved configurations still load.
- Parameter-name hints moved to the declarative inlay API, because the whole
  `codeInsight.hints` package is `@ApiStatus.Experimental`. The setting now lives under
  Settings | Editor | Inlay Hints | Parameter names | MQL. The per-method "don't show hints for"
  blacklist is gone; Print/PrintFormat/Alert/Comment stay excluded in code.

javac now runs with `-Xlint:deprecation -Xlint:removal -Werror`, so new deprecated calls fail the build.

## All accepted gaps fixed (2026-11-14, branch `fix/clean-pass`)

Commits `5c8b90b` (parser), `1bab5b1` (resolver), `2d95c36` (inspections), `0e19ff0` (completion and
structure). 525 tests. Stub schema 26. Verifier: Compatible on IU 2025.3.2 and CL 2026.3, with only
the known `suggestHomePath` override.

| Gap | Fix |
|---|---|
| S-2 union | `CLASS` of kind Union. The AST class kind also fixed: interfaces used to read as classes |
| S-3 / N-1 namespaces | `NAMESPACE_BLOCK` whose body holds file-level PSI and stubs; `Ns::name` resolves; inspections walk namespace bodies |
| S-4 input group | `INPUT_GROUP` node with a keyword-colored `group`; structure view shows each group with its inputs |
| S-5 offsetof | keyword-colored before `(`; `m` in `offsetof(S, m)` resolves to S's member |
| T-3 trailing-dot floats | `5.`, `5.e2` lex as one number |
| T-4 typedef | stub-indexed `TYPEDEF` named by `(*Name)`; resolves and completes |
| T-5 vector/matrix | keyword-colored in MQL5; members complete from a MetaEditor-verified name list (`mql/doc/mql5-vector-matrix.json`) |
| O-1 | `arr[i].m` uses the element type; `Get().m` uses the return type |
| O-2 operators | `operator==`, `operator[]`, `operator()`... and `Type *Name()` are functions |
| V-2 | `::name` skips locals |
| V-3 | MQL5 `extern int x = 3;` is error 303 |
| OOP-1 | out-of-line `X::Method` bodies and `this` see class X |
| OOP-2 | `int C::s = 0;` resolves to the static field |
| P-1 | `#define` is a stub-indexed element; names resolve and complete; macro parameters resolve to nothing |
| I-2, I-5, F-3, F-4 | see commit `2d95c36` |
| review items | `'\99999'` is error 239 and `"\99999"` warning 85 (MetaEditor's texts); the declaration list scans each initializer once; `a * b;` with a variable `a` is not a declaration |

Gate after: rigg PARSE 0, BADCHAR 0, RESOLVED 34,785 of 49,153 (was 32,991 of 49,388; the total fell by
the 209 `#define` names and 26 `group` keywords that are now declarations or syntax). trade RESOLVED
2,128 of 3,757 (was 1,641), mostly the 289 out-of-line method bodies.

**D-1** resolved by the owner's choice (option 3, commit `83f5b53`): in MQL5 files, quick doc for
language-reference entries (links under `/basis/`: 55 keywords, 9 preprocessor directives, the 3
`INIT_*` constants) shows nothing instead of the MQL4 page. MQL4 files keep them; function and
constant pages are unchanged. No mql5.com text was imported.
