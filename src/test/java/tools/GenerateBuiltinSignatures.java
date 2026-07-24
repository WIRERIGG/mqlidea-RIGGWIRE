/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package tools;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;

import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * One-off generator (REVAMP_PLAN.md Phase 6, deliverable 1): reads
 * {@code src/main/resources/mql/doc/mql4-functions.json} (558 [name, link] pairs) and the bundled
 * doc HTML pages under {@code src/main/resources/mql/doc/en/}, extracts each function's formal
 * signature from the first "syntax box" on its page, and writes
 * {@code src/main/resources/mql/doc/mql4-signatures.json}.
 *
 * <p>Deliberately NOT a JUnit test (no {@code @Test} methods, so {@code gradle test} never runs
 * it) and has zero IntelliJ-platform dependency -- it is plain text/JSON processing, run once by
 * hand via {@code javac}/{@code java} against the gson jar already on the test classpath, with its
 * committed OUTPUT ({@code mql4-signatures.json}) checked in so the plugin never parses HTML at
 * runtime.</p>
 *
 * <p>Usage: {@code java -cp gson.jar:tools tools.GenerateBuiltinSignatures <repoRoot>}</p>
 */
public final class GenerateBuiltinSignatures {

    private static final Pattern TD_OPEN = Pattern.compile("<td[^>]*>");
    private static final Pattern BR = Pattern.compile("(?i)<br\\s*/?>");
    private static final Pattern TAG = Pattern.compile("<[^>]+>");
    private static final Pattern WS = Pattern.compile("\\s+");

    private GenerateBuiltinSignatures() {
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: GenerateBuiltinSignatures <repoRoot>");
            System.exit(1);
        }
        Path repoRoot = Path.of(args[0]);
        Path resources = repoRoot.resolve("src/main/resources/mql/doc");
        Path functionsJson = resources.resolve("mql4-functions.json");
        Path enDir = resources.resolve("en");
        Path outFile = resources.resolve("mql4-signatures.json");

        List<String[]> catalog = readCatalog(functionsJson);
        List<Signature> results = new ArrayList<>();
        int missingPage = 0;
        int parseFailed = 0;
        for (String[] entry : catalog) {
            String name = entry[0];
            String link = entry[1];
            Path htmlFile = enDir.resolve(link.replaceFirst("^/", "") + ".html");
            if (!Files.exists(htmlFile)) {
                missingPage++;
                continue;
            }
            String html = Files.readString(htmlFile, StandardCharsets.UTF_8);
            Signature sig = parseSignature(name, html);
            if (sig == null) {
                parseFailed++;
                continue;
            }
            results.add(sig);
        }

        results.sort((a, b) -> a.name.compareTo(b.name));
        writeJson(outFile, results);

        System.out.println("catalog entries: " + catalog.size());
        System.out.println("signatures extracted: " + results.size());
        System.out.println("missing doc page: " + missingPage);
        System.out.println("parse failed: " + parseFailed);
        System.out.println("wrote: " + outFile);
    }

    private static List<String[]> readCatalog(Path functionsJson) throws IOException {
        List<String[]> out = new ArrayList<>();
        try (Reader reader = Files.newBufferedReader(functionsJson, StandardCharsets.UTF_8)) {
            Gson gson = new GsonBuilder().create();
            JsonArray arr = gson.fromJson(reader, JsonArray.class);
            for (JsonElement el : arr) {
                JsonArray pair = el.getAsJsonArray();
                out.add(new String[]{pair.get(0).getAsString(), pair.get(1).getAsString()});
            }
        }
        return out;
    }

    /**
     * Extracts the text of the FIRST "syntax box" {@code <td>} on the page (the doc pages always
     * put the formal signature there, before the "Parameters"/"Example" sections which reuse the
     * same box styling further down).
     */
    static Signature parseSignature(String name, String html) {
        Matcher tdMatcher = TD_OPEN.matcher(html);
        if (!tdMatcher.find()) {
            return null;
        }
        int contentStart = tdMatcher.end();
        int contentEnd = html.indexOf("</td>", contentStart);
        if (contentEnd < 0) {
            return null;
        }
        String box = html.substring(contentStart, contentEnd);
        box = BR.matcher(box).replaceAll("\n");
        box = TAG.matcher(box).replaceAll("");
        box = decodeEntities(box);

        StringBuilder joined = new StringBuilder();
        for (String line : box.split("\n")) {
            String trimmed = stripLineComment(line).trim();
            if (!trimmed.isEmpty()) {
                if (joined.length() > 0) {
                    joined.append(' ');
                }
                joined.append(trimmed);
            }
        }
        String full = WS.matcher(joined.toString()).replaceAll(" ").trim();
        if (full.endsWith(";")) {
            full = full.substring(0, full.length() - 1).trim();
        }

        int openParen = full.indexOf('(');
        if (openParen < 0) {
            return null; // not a function signature (e.g. a #define/constant page)
        }
        String head = full.substring(0, openParen).trim();
        int closeParen = matchingCloseParen(full, openParen);
        if (closeParen < 0) {
            return null;
        }
        String paramsStr = full.substring(openParen + 1, closeParen).trim();

        String returnType;
        String[] headParts = head.split("\\s+");
        if (headParts.length == 0 || headParts[headParts.length - 1].isEmpty()) {
            return null;
        }
        String headName = headParts[headParts.length - 1];
        if (!headName.equals(name)) {
            // Page title/link mismatch or an overload with a differently-cased/qualified name --
            // still usable as long as it looks like a real declaration head.
        }
        returnType = headParts.length > 1 ? String.join(" ", java.util.Arrays.copyOf(headParts, headParts.length - 1)) : "";

        List<String> params = splitTopLevel(paramsStr);
        String signature = (returnType.isEmpty() ? "" : returnType + " ") + name + "(" + String.join(", ", params) + ")";
        return new Signature(name, returnType, params, signature);
    }

    private static String stripLineComment(String line) {
        int idx = line.indexOf("//");
        return idx >= 0 ? line.substring(0, idx) : line;
    }

    private static String decodeEntities(String s) {
        return s.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", "\"");
    }

    private static int matchingCloseParen(String s, int openIdx) {
        int depth = 0;
        for (int i = openIdx; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '(') {
                depth++;
            } else if (c == ')') {
                depth--;
                if (depth == 0) {
                    return i;
                }
            }
        }
        return -1;
    }

    /** Splits on commas that are not nested inside (), [] -- default-value expressions rarely nest, but be safe. */
    private static List<String> splitTopLevel(String s) {
        List<String> parts = new ArrayList<>();
        if (s.isEmpty()) {
            return parts;
        }
        int depth = 0;
        int start = 0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '(' || c == '[') {
                depth++;
            } else if (c == ')' || c == ']') {
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

    private static void writeJson(Path outFile, List<Signature> results) throws IOException {
        Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
        String json = gson.toJson(results);
        Files.writeString(outFile, json, StandardCharsets.UTF_8);
    }

    /** Mirrors {@code com.limemojito.oss.mql.doc.BuiltinSignature}'s JSON shape exactly (kept dependency-free here). */
    static final class Signature {
        String name;
        String returnType;
        List<String> params;
        String signature;

        Signature(String name, String returnType, List<String> params, String signature) {
            this.name = name;
            this.returnType = returnType;
            this.params = params;
            this.signature = signature;
        }
    }
}
