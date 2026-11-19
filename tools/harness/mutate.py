#!/usr/bin/env python3
"""Mutation set for the plugin harness (specs/001-metaeditor-harness, FR-017 and FR-021).

Injects one known error into a copy of a program. Sites come from the raw text and a simple
token scan only (comments and strings blanked out), never from the plugin's parser or resolver,
so the sample isn't biased toward code the plugin already understands. Seeded: the same program
text, seed and kind always give the same mutants. Mutants are written to /tmp by the referee,
never into a repository; MetaEditor decides which ones count (a mutant it accepts is dropped).

    mutate(text, kind, seed, count) -> [Mutant(kind, line, text)]
"""

import random
import re
from collections import namedtuple

Mutant = namedtuple("Mutant", "kind line text")  # line: 1-based line of the injected error

KINDS = ("missing-semicolon", "misspelt-identifier", "wrong-argument-count", "type-mismatch",
         "unbalanced-brace", "undeclared-member")

KEYWORDS = set("""
    if else for while do switch case default break continue return goto sizeof new delete this
    operator class struct union enum interface template typename namespace public private protected
    virtual override final static const input sinput extern export import true false NULL void bool
    char uchar short ushort int uint long ulong float double string datetime color vector matrix
    complex typedef offsetof EMPTY_VALUE WRONG_VALUE
""".split())

# Builtins whose argument count varies (variadic, or with defaults on every parameter).
VARIADIC = {"Print", "PrintFormat", "StringFormat", "Comment", "Alert", "printf", "FileWrite",
            "StringConcatenate", "ZeroMemory", "ArrayPrint", "MathMax", "MathMin", "fmax", "fmin"}

PASTE = "Zq"  # appended to a name: never a real identifier in the corpus


def mask(text):
    """`text` with comments, string and char literals blanked to spaces (newlines kept), so
    positions line up with the original and no site lands inside them."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "//":
            j = text.find("\n", i)
            j = n if j < 0 else j
        elif two == "/*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
        elif c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
        else:
            i += 1
            continue
        for k in range(i, j):
            if out[k] != "\n":
                out[k] = " "
        i = j
    return "".join(out)


def _line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def _preprocessor_lines(masked):
    """Line numbers of preprocessor directives, including continued #define lines."""
    lines, cont = set(), False
    for no, line in enumerate(masked.split("\n"), 1):
        if cont or line.lstrip().startswith("#"):
            lines.add(no)
            cont = line.rstrip().endswith("\\")
        else:
            cont = False
    return lines


def _sites(text, masked, kind):
    """Candidate (start, end, replacement) edits for `kind`."""
    pp = _preprocessor_lines(masked)
    ok = lambda m: _line_of(masked, m.start()) not in pp
    sites = []
    if kind == "missing-semicolon":
        # a statement's ';' at the end of a line (not inside for(;;))
        for m in re.finditer(r";[ \t]*(?=\n)", masked):
            line_start = masked.rfind("\n", 0, m.start()) + 1
            if ok(m) and "for" not in masked[line_start:m.start()].split("(")[0]:
                sites.append((m.start(), m.start() + 1, ""))
    elif kind == "misspelt-identifier":
        seen = set()
        for m in re.finditer(r"\b[A-Za-z_]\w*\b", masked):
            name = m.group()
            if not ok(m):
                continue  # a macro body's use doesn't declare the name
            first = name not in seen
            seen.add(name)
            prev = masked[:m.start()].rstrip()[-1:]
            if first or name in KEYWORDS or prev in (".", ">", ":"):
                continue  # the first use outside the preprocessor is likely the declaration
            sites.append((m.start(), m.end(), name + PASTE))
    elif kind == "wrong-argument-count":
        for m in re.finditer(r"\b([A-Za-z_]\w*)[ \t]*\(([^()\n]*)\)[ \t]*;", masked):
            name, args = m.group(1), m.group(2)
            prev = masked[:m.start()].rstrip()[-1:]
            if name in KEYWORDS or name in VARIADIC or prev in (".", ">") or not ok(m):
                continue
            # a call statement: Name(args); with nothing but whitespace or '=' before it on the line
            line_start = masked.rfind("\n", 0, m.start()) + 1
            before = masked[line_start:m.start()]
            if before.strip() and not re.search(r"=\s*$", before):
                continue
            close = m.start(2) + len(args)
            sites.append((close, close, (", " if args.strip() else "") + "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0"))
    elif kind == "type-mismatch":
        # a pointer or object gets a number: p = new CFoo(...);  ->  p = 1.5;
        for m in re.finditer(r"=[ \t]*(new\b[^;\n]*);", masked):
            if ok(m):
                sites.append((m.start(1), m.end(1), "1.5"))
        # a number gets an object: int x = 5;  ->  int x = new CObject;  is too clever; instead
        # a numeric declaration gets an array initialiser, which no scalar accepts
        for m in re.finditer(r"\b(?:int|uint|long|ulong|double|float|short|ushort|char|uchar|bool|datetime)"
                             r"[ \t]+[A-Za-z_]\w*[ \t]*=[ \t]*([^;{}\n,]+);", masked):
            if ok(m):
                sites.append((m.start(1), m.end(1), "{1, 2}"))
    elif kind == "unbalanced-brace":
        for m in re.finditer(r"(?m)^[ \t]*(\})[ \t;]*$", masked):
            if ok(m):
                sites.append((m.start(1), m.end(1), ""))
    elif kind == "undeclared-member":
        for m in re.finditer(r"\b[A-Za-z_]\w*(?:\.|->)([A-Za-z_]\w*)\b", masked):
            if ok(m) and not m.group(1)[0].isdigit():
                sites.append((m.start(1), m.end(1), m.group(1) + PASTE))
    else:
        raise ValueError(kind)
    return sites


def mutate(text, kind, seed, count):
    """Up to `count` mutants of `text` for `kind`, at distinct seeded sites, in line order."""
    masked = mask(text)
    sites = _sites(text, masked, kind)
    rng = random.Random(f"{seed}:{kind}:{len(text)}:{text[:200]}")
    picked = sorted(rng.sample(sites, min(count, len(sites))))
    return [Mutant(kind, _line_of(text, start), text[:start] + repl + text[end:]) for start, end, repl in picked]


def self_test():
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)

    src = ('#include <Trade\\Trade.mqh>\n'
           '#define CALL(x) Foo(x);\n'
           'CTrade trade;\n'
           'int Foo(int a) { return a; }\n'
           'void OnStart()\n'
           '  {\n'
           '   int total = 3; // a comment; with Foo(1);\n'
           '   string s = "Foo(2); }";\n'
           '   Foo(total);\n'
           '   CObject *o = new CObject();\n'
           '   for(int i = 0; i < total; i++)\n'
           '     {\n'
           '      trade.Buy(0.1);\n'
           '     }\n'
           '   delete o;\n'
           '  }\n')
    check("mask keeps length", len(mask(src)) == len(src))
    check("mask blanks strings and comments", "Foo(2)" not in mask(src) and "a comment" not in mask(src))
    for kind in KINDS:
        ms = mutate(src, kind, 7, 50)
        check(f"{kind}: has sites", len(ms) > 0)
        check(f"{kind}: seeded", ms == mutate(src, kind, 7, 50))
        check(f"{kind}: one edit each", all(m.text != src for m in ms))
        check(f"{kind}: never on a preprocessor line", all(m.line not in (1, 2) for m in ms))
        check(f"{kind}: never in a comment or string", all(m.line != 8 or kind == "missing-semicolon" for m in ms))
        for m in ms:
            changed = [no for no, (a, b) in enumerate(zip(src.split("\n"), m.text.split("\n")), 1) if a != b]
            check(f"{kind}: reported line is the changed line", changed[:1] == [m.line])
    check("missing ; skips for(;;)", all(m.line != 11 for m in mutate(src, "missing-semicolon", 1, 50)))
    check("misspelt skips the first use", all("int Foo" + PASTE not in m.text for m in mutate(src, "misspelt-identifier", 1, 50)))
    check("member after a dot", any("trade.Buy" + PASTE in m.text for m in mutate(src, "undeclared-member", 1, 50)))
    check("pointer gets a number", any("= 1.5;" in m.text for m in mutate(src, "type-mismatch", 1, 50)))
    check("argument count", any("Foo(total, 0" in m.text for m in mutate(src, "wrong-argument-count", 1, 50)))
    check("count respected", len(mutate(src, "misspelt-identifier", 1, 2)) == 2)
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("mutate self-test passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(self_test())
