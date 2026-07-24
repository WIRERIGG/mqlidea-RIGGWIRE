/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package tools;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/**
 * One-off generator (REVAMP_PLAN.md Phase 6, deliverable 2): scrapes the real MQL5 Standard
 * Library {@code Include/*.mqh} headers (CTrade, CArrayObj, CPositionInfo, COrderInfo,
 * CSymbolInfo, CAccountInfo, CObject, ...) for public class methods and writes
 * {@code src/main/resources/mql/doc/mql5-stdlib.json}. The bundled doc HTML corpus has no
 * Standard Library class pages (checked: no {@code standardlibrary/} folder under
 * {@code mql/doc/en/}), so the headers themselves -- shipped with every MetaTrader 5 install --
 * are the only usable source; this closes the CTrade/CArray/CPositionInfo completion gap flagged
 * in the Phase 4/5 reviews.
 *
 * <p>Only files whose header still carries "MetaQuotes" copyright are scraped (filters out
 * project-specific {@code .mqh} files that may share the same {@code Include/} tree on a
 * developer machine, e.g. an EA's own risk-manager headers), and template classes ({@code
 * Generic/*.mqh}) are skipped -- generics need a type-substitution model this tool doesn't
 * attempt; see the class javadoc note in the committed output for the resulting gap.</p>
 *
 * <p>Deliberately NOT a JUnit test and has zero IntelliJ-platform dependency; run once by hand:
 * {@code java -cp gson.jar:tools tools.GenerateStdlibCatalog <mql5IncludeRoot> <repoRoot>}</p>
 */
public final class GenerateStdlibCatalog {

    private static final Pattern BLOCK_COMMENT = Pattern.compile("/\\*.*?\\*/", Pattern.DOTALL);
    private static final Pattern LINE_COMMENT = Pattern.compile("//[^\n]*");
    private static final Pattern CLASS_DECL = Pattern.compile(
            "(template\\s*<[^>]*>\\s*)?class\\s+(\\w+)(\\s*:\\s*(public|protected|private)\\s+([\\w:<>,\\s]+?))?\\s*\\{");
    private static final Pattern METHOD_HEAD_WITH_TYPE = Pattern.compile("^(.+?)\\s+([A-Za-z_]\\w*)\\s*\\(([\\s\\S]*)\\)\\s*(const)?\\s*$");
    private static final Pattern METHOD_HEAD_CTOR = Pattern.compile("^(~?[A-Za-z_]\\w*)\\s*\\(([\\s\\S]*)\\)\\s*(const)?\\s*$");

    private GenerateStdlibCatalog() {
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.err.println("usage: GenerateStdlibCatalog <mql5IncludeRoot> <repoRoot>");
            System.exit(1);
        }
        Path includeRoot = Path.of(args[0]);
        Path repoRoot = Path.of(args[1]);
        Path outFile = repoRoot.resolve("src/main/resources/mql/doc/mql5-stdlib.json");

        List<Path> files;
        try (Stream<Path> walk = Files.walk(includeRoot)) {
            files = walk.filter(p -> p.getFileName().toString().toLowerCase().endsWith(".mqh"))
                    .filter(GenerateStdlibCatalog::looksLikeGenuineStandardLibraryFile)
                    .sorted()
                    .toList();
        }

        List<ClassEntry> allClasses = new ArrayList<>();
        int templateClassesSkipped = 0;
        for (Path file : files) {
            String relative = includeRoot.relativize(file).toString().replace('\\', '/');
            String raw = Files.readString(file, StandardCharsets.UTF_8);
            String stripped = stripComments(raw);

            Matcher m = CLASS_DECL.matcher(stripped);
            int searchFrom = 0;
            while (searchFrom <= stripped.length() && m.find(searchFrom)) {
                boolean isTemplate = m.group(1) != null;
                String className = m.group(2);
                String parentRaw = m.group(5);
                int bodyOpenBrace = m.end() - 1;
                int bodyCloseBrace = matchingCloseBrace(stripped, bodyOpenBrace);
                if (bodyCloseBrace < 0) {
                    break; // malformed/unbalanced -- stop scanning this file
                }
                if (isTemplate) {
                    templateClassesSkipped++;
                } else {
                    String body = stripped.substring(bodyOpenBrace + 1, bodyCloseBrace);
                    String parent = firstIdentifier(parentRaw);
                    List<MethodEntry> methods = extractPublicMethods(body);
                    allClasses.add(new ClassEntry(className, parent, relative, methods));
                }
                searchFrom = bodyCloseBrace + 1;
            }
        }

        allClasses.sort((a, b) -> a.name.compareTo(b.name));
        writeJson(outFile, allClasses);

        int totalMethods = allClasses.stream().mapToInt(c -> c.methods.size()).sum();
        long classesWithMethods = allClasses.stream().filter(c -> !c.methods.isEmpty()).count();
        System.out.println("standard-library files scanned: " + files.size());
        System.out.println("classes extracted: " + allClasses.size() + " (" + classesWithMethods + " with >=1 public method)");
        System.out.println("template classes skipped (Generic<T> collections -- gap, see javadoc): " + templateClassesSkipped);
        System.out.println("total public methods/constructors: " + totalMethods);
        System.out.println("wrote: " + outFile);
    }

    /** MetaQuotes copyright is the signal that separates the real Standard Library from a developer's own project headers. */
    private static boolean looksLikeGenuineStandardLibraryFile(Path file) {
        try {
            String head = Files.readString(file, StandardCharsets.UTF_8);
            return head.contains("MetaQuotes");
        } catch (IOException e) {
            return false;
        }
    }

    private static String stripComments(String text) {
        String noBlock = BLOCK_COMMENT.matcher(text).replaceAll("");
        return LINE_COMMENT.matcher(noBlock).replaceAll("");
    }

    private static int matchingCloseBrace(String text, int openIdx) {
        int depth = 0;
        for (int i = openIdx; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '{') {
                depth++;
            } else if (c == '}') {
                depth--;
                if (depth == 0) {
                    return i;
                }
            }
        }
        return -1;
    }

    private static String firstIdentifier(String parentRaw) {
        if (parentRaw == null) {
            return null;
        }
        Matcher m = Pattern.compile("(\\w+)").matcher(parentRaw);
        return m.find() ? m.group(1) : null;
    }

    /**
     * Splits the class body (already brace-balanced, comments stripped) into top-level member
     * statements by walking brace depth, tracks the current access-label section, and keeps only
     * methods/constructors declared while {@code public:} is in effect. See the generator's class
     * javadoc for the depth-walk rationale.
     */
    private static List<MethodEntry> extractPublicMethods(String body) {
        List<MethodEntry> methods = new ArrayList<>();
        String access = "private"; // MQL5 'class' defaults to private, same as C++
        boolean skipNext = false; // true right after a constructor's member-initializer-list ':' was seen
        int depth = 0;
        StringBuilder buf = new StringBuilder();
        for (int i = 0; i < body.length(); i++) {
            char c = body.charAt(i);
            buf.append(c);
            if (c == '{') {
                depth++;
                continue;
            }
            if (c == '}') {
                depth--;
                if (depth == 0) {
                    FlushResult r = flush(buf, access, skipNext, methods);
                    access = r.access;
                    skipNext = r.skipNext;
                }
                continue;
            }
            if (depth == 0 && (c == ';' || c == ':')) {
                FlushResult r = flush(buf, access, skipNext, methods);
                access = r.access;
                skipNext = r.skipNext;
            }
        }
        return methods;
    }

    private record FlushResult(String access, boolean skipNext) {
    }

    /**
     * Handles one flushed top-level statement: an access label, a candidate method (if currently
     * public), or -- if {@code skipNext} is set -- the discarded remainder of a constructor's
     * member-initializer list (the segment between its ':' and its body's '{'), which otherwise
     * gets mistaken for a second, malformed method signature (see {@link #stripAfterTopLevelColon}).
     */
    private static FlushResult flush(StringBuilder buf, String currentAccess, boolean skipNext, List<MethodEntry> methods) {
        String raw = buf.toString();
        buf.setLength(0);
        char boundary = raw.isEmpty() ? '\0' : raw.charAt(raw.length() - 1);
        if (raw.isEmpty()) {
            return new FlushResult(currentAccess, false);
        }
        if (skipNext) {
            return new FlushResult(currentAccess, false); // discard the initializer-list remainder
        }
        String content = raw.substring(0, raw.length() - 1).trim(); // drop the trailing boundary char (';', '}' or ':')
        if (content.isEmpty()) {
            return new FlushResult(currentAccess, false);
        }
        if (content.equals("public") || content.equals("protected") || content.equals("private")) {
            return new FlushResult(content, false);
        }
        if (!"public".equals(currentAccess)) {
            return new FlushResult(currentAccess, false);
        }
        int firstBrace = content.indexOf('{');
        String head = (firstBrace >= 0 ? content.substring(0, firstBrace) : content).trim();
        boolean hasInitializerList = boundary == ':' && head.contains("(");
        head = stripAfterTopLevelColon(head).trim();
        if (!head.contains("(")) {
            return new FlushResult(currentAccess, false); // a field, not a method
        }
        MethodEntry method = parseMethodHead(head);
        if (method != null && !method.name.startsWith("~")) {
            methods.add(method);
        }
        return new FlushResult(currentAccess, hasInitializerList);
    }

    private static String stripAfterTopLevelColon(String head) {
        int parenDepth = 0;
        for (int i = 0; i < head.length(); i++) {
            char c = head.charAt(i);
            if (c == '(') {
                parenDepth++;
            } else if (c == ')') {
                parenDepth--;
            } else if (c == ':' && parenDepth == 0) {
                return head.substring(0, i);
            }
        }
        return head;
    }

    private static final Pattern LEADING_MODIFIERS = Pattern.compile("^(virtual|static)\\s+");

    private static String stripLeadingModifiers(String returnType) {
        String s = returnType;
        Matcher m;
        while ((m = LEADING_MODIFIERS.matcher(s)).find()) {
            s = s.substring(m.end());
        }
        return s;
    }

    private static MethodEntry parseMethodHead(String head) {
        Matcher withType = METHOD_HEAD_WITH_TYPE.matcher(head);
        if (withType.matches()) {
            String returnType = stripLeadingModifiers(withType.group(1).trim());
            String name = withType.group(2).trim();
            List<String> params = splitTopLevel(withType.group(3).trim());
            boolean ctor = false;
            String signature = returnType + " " + name + "(" + String.join(", ", params) + ")";
            return new MethodEntry(name, returnType, params, signature, ctor);
        }
        Matcher ctorMatcher = METHOD_HEAD_CTOR.matcher(head);
        if (ctorMatcher.matches()) {
            String name = ctorMatcher.group(1).trim();
            List<String> params = splitTopLevel(ctorMatcher.group(2).trim());
            String signature = name + "(" + String.join(", ", params) + ")";
            return new MethodEntry(name, "", params, signature, true);
        }
        return null;
    }

    private static List<String> splitTopLevel(String s) {
        List<String> parts = new ArrayList<>();
        if (s.isEmpty()) {
            return parts;
        }
        int depth = 0;
        int start = 0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '(' || c == '[' || c == '<') {
                depth++;
            } else if (c == ')' || c == ']' || c == '>') {
                depth--;
            } else if (c == ',' && depth == 0) {
                parts.add(s.substring(start, i).trim());
                start = i + 1;
            }
        }
        String last = s.substring(start).trim();
        if (!last.isEmpty()) {
            parts.add(last);
        }
        return parts;
    }

    private static void writeJson(Path outFile, List<ClassEntry> classes) throws IOException {
        // Compact (not pretty-printed): ~516 classes / ~7,000 methods pretty-prints to several MB;
        // this is a machine-loaded runtime resource, not something reviewed line-by-line.
        Gson gson = new GsonBuilder().disableHtmlEscaping().create();
        Files.writeString(outFile, gson.toJson(classes), StandardCharsets.UTF_8);
    }

    /** Mirrors {@code com.limemojito.oss.mql.doc.StdLibClass}'s JSON shape exactly (kept dependency-free here). */
    static final class ClassEntry {
        String name;
        String parent;
        String file;
        List<MethodEntry> methods;

        ClassEntry(String name, String parent, String file, List<MethodEntry> methods) {
            this.name = name;
            this.parent = parent;
            this.file = file;
            this.methods = methods;
        }
    }

    /** Mirrors {@code com.limemojito.oss.mql.doc.StdLibMethod}'s JSON shape exactly. */
    static final class MethodEntry {
        String name;
        String returnType;
        List<String> params;
        String signature;
        boolean isConstructor;

        MethodEntry(String name, String returnType, List<String> params, String signature, boolean isConstructor) {
            this.name = name;
            this.returnType = returnType;
            this.params = params;
            this.signature = signature;
            this.isConstructor = isConstructor;
        }
    }
}
