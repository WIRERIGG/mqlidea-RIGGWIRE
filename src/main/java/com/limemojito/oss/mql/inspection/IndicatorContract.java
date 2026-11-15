/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.psi.PsiFile;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * What an indicator's source declares about its buffers, read from literal values only:
 * {@code #property indicator_buffers/plots/typeN}, {@code SetIndexBuffer(i, b, type)} calls and
 * its {@code input}s. Anything computed (a non-literal index, {@code PlotIndexSetInteger(..,
 * PLOT_DRAW_TYPE, ..)}, a draw type with a variable buffer count) makes the dependent facts
 * unknown, and the checks built on them stay silent.
 */
final class IndicatorContract {

    /** One {@code SetIndexBuffer(index, array, type)} call with a literal index. */
    record Binding(int index, @NotNull String type, int offset) {
        boolean isData() {
            return "INDICATOR_DATA".equals(type) || "INDICATOR_COLOR_INDEX".equals(type);
        }
    }

    /**
     * Buffers each draw type consumes (MQL5 reference, Drawing Styles). DRAW_BARS and
     * DRAW_CANDLES are absent: they may be drawn from fewer than four buffers.
     */
    private static final Map<String, Integer> BUFFERS_PER_DRAW_TYPE = Map.ofEntries(
            Map.entry("DRAW_NONE", 1), Map.entry("DRAW_LINE", 1), Map.entry("DRAW_SECTION", 1),
            Map.entry("DRAW_HISTOGRAM", 1), Map.entry("DRAW_ARROW", 1), Map.entry("DRAW_HISTOGRAM2", 2),
            Map.entry("DRAW_ZIGZAG", 2), Map.entry("DRAW_FILLING", 2), Map.entry("DRAW_COLOR_LINE", 2),
            Map.entry("DRAW_COLOR_SECTION", 2), Map.entry("DRAW_COLOR_HISTOGRAM", 2), Map.entry("DRAW_COLOR_ARROW", 2),
            Map.entry("DRAW_COLOR_HISTOGRAM2", 3), Map.entry("DRAW_COLOR_ZIGZAG", 3), Map.entry("DRAW_COLOR_BARS", 5),
            Map.entry("DRAW_COLOR_CANDLES", 5));

    private static final Pattern BUFFERS = Pattern.compile("#property\\s+indicator_buffers\\s+(\\d+)");
    private static final Pattern PLOTS = Pattern.compile("#property\\s+indicator_plots\\s+(\\d+)");
    private static final Pattern PLOT_TYPE = Pattern.compile("#property\\s+indicator_type(\\d+)\\s+(\\w+)");
    private static final Pattern SET_INDEX_BUFFER = Pattern.compile(
            "\\bSetIndexBuffer\\s*\\(\\s*([^,()]+?)\\s*,\\s*[\\w.]+\\s*(?:,\\s*(\\w+)\\s*)?\\)");
    private static final Pattern DYNAMIC_DRAW_TYPE = Pattern.compile("\\bPLOT_DRAW_TYPE\\b");
    private static final Pattern INPUT = Pattern.compile("(?m)^[ \\t]*(?:input|sinput)\\s+(?!group\\b)([^;]*);");
    private static final Pattern ON_CALCULATE = Pattern.compile("\\bint\\s+OnCalculate\\s*\\(([^)]*)\\)");

    /** {@code indicator_buffers}, or -1 when it isn't a literal. */
    final int buffers;
    /** {@code indicator_plots}, or -1. */
    final int plots;
    /** Buffers the plots consume ({@code 26 plots = buffers 0-27}), or -1 when a draw type is unknown. */
    final int plotBuffers;
    /** Literal-index bindings, in source order. */
    final List<Binding> bindings;
    /** True when some {@code SetIndexBuffer} index isn't a literal. */
    final boolean dynamicBindings;
    /**
     * Number of {@code input}/{@code sinput} parameters across the file's {@code #include} closure,
     * or -1 when a line declares several or an include doesn't resolve.
     */
    final int inputs;
    /** True for {@code OnCalculate(rates_total, prev_calculated, begin, price[])}: iCustom may pass one more argument. */
    final boolean shortOnCalculate;

    private IndicatorContract(int buffers, int plots, int plotBuffers, List<Binding> bindings, boolean dynamicBindings,
                              int inputs, boolean shortOnCalculate) {
        this.buffers = buffers;
        this.plots = plots;
        this.plotBuffers = plotBuffers;
        this.bindings = bindings;
        this.dynamicBindings = dynamicBindings;
        this.inputs = inputs;
        this.shortOnCalculate = shortOnCalculate;
    }

    /** The binding of buffer {@code index}, or null. */
    @Nullable
    Binding binding(int index) {
        for (Binding b : bindings) {
            if (b.index == index) {
                return b;
            }
        }
        return null;
    }

    /** The contract of {@code file}, or null when it isn't an indicator ({@code indicator_buffers} and {@code SetIndexBuffer} absent). */
    @Nullable
    static IndicatorContract of(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            IndicatorContract own = parse(code(file.getViewProvider().getContents()));
            IndicatorContract contract = own == null ? null : own.withInputs(closureInputs(file));
            return CachedValueProvider.Result.create(contract, PsiModificationTracker.MODIFICATION_COUNT);
        });
    }

    @NotNull
    private IndicatorContract withInputs(int count) {
        return new IndicatorContract(buffers, plots, plotBuffers, bindings, dynamicBindings, count, shortOnCalculate);
    }

    /** Inputs are counted in every file the indicator compiles with: an included header can declare some. */
    private static int closureInputs(@NotNull PsiFile root) {
        java.util.Set<PsiFile> visited = new java.util.LinkedHashSet<>();
        java.util.Deque<PsiFile> queue = new java.util.ArrayDeque<>();
        visited.add(root);
        queue.add(root);
        int total = 0;
        while (!queue.isEmpty()) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            PsiFile current = queue.poll();
            int own = inputs(code(current.getViewProvider().getContents()));
            if (own < 0) {
                return -1;
            }
            total += own;
            for (com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock include
                    : com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(current, com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock.class)) {
                PsiFile target = include.resolveIncludedFile();
                if (target == null) {
                    return -1;
                }
                if (visited.add(target)) {
                    queue.add(target);
                }
            }
        }
        return total;
    }

    @Nullable
    static IndicatorContract parse(@NotNull String code) {
        Matcher buffersMatch = BUFFERS.matcher(code);
        boolean declaresBuffers = buffersMatch.find();
        List<Binding> bindings = new ArrayList<>();
        boolean dynamic = false;
        Matcher m = SET_INDEX_BUFFER.matcher(code);
        while (m.find()) {
            String index = m.group(1);
            if (index.matches("\\d+")) {
                bindings.add(new Binding(Integer.parseInt(index), m.group(2) == null ? "INDICATOR_DATA" : m.group(2), m.start(1)));
            } else {
                dynamic = true;
            }
        }
        if (!declaresBuffers && bindings.isEmpty() && !dynamic) {
            return null;
        }
        int buffers = declaresBuffers ? Integer.parseInt(buffersMatch.group(1)) : -1;
        Matcher plotsMatch = PLOTS.matcher(code);
        int plots = plotsMatch.find() ? Integer.parseInt(plotsMatch.group(1)) : -1;
        return new IndicatorContract(buffers, plots, plotBuffers(code, plots), bindings, dynamic,
                inputs(code), shortOnCalculate(code));
    }

    private static int plotBuffers(@NotNull String code, int plots) {
        if (plots < 0 || DYNAMIC_DRAW_TYPE.matcher(code).find()) {
            return -1;
        }
        Map<Integer, String> types = new TreeMap<>();
        Matcher m = PLOT_TYPE.matcher(code);
        while (m.find()) {
            if (types.put(Integer.parseInt(m.group(1)), m.group(2)) != null) {
                return -1; // declared twice (#ifdef branches): unknown
            }
        }
        int total = 0;
        for (int plot = 1; plot <= plots; plot++) {
            Integer count = BUFFERS_PER_DRAW_TYPE.get(types.get(plot));
            if (count == null) {
                return -1; // missing type or one with a variable buffer count
            }
            total += count;
        }
        return total;
    }

    private static int inputs(@NotNull String code) {
        int count = 0;
        Matcher m = INPUT.matcher(code);
        while (m.find()) {
            if (topLevelComma(m.group(1))) {
                return -1; // input int a = 1, b = 2;
            }
            count++;
        }
        return count;
    }

    private static boolean topLevelComma(@NotNull String declaration) {
        int depth = 0;
        for (int i = 0; i < declaration.length(); i++) {
            char c = declaration.charAt(i);
            if (c == '(' || c == '{' || c == '[') {
                depth++;
            } else if (c == ')' || c == '}' || c == ']') {
                depth--;
            } else if (c == ',' && depth == 0) {
                return true;
            }
        }
        return false;
    }

    private static boolean shortOnCalculate(@NotNull String code) {
        Matcher m = ON_CALCULATE.matcher(code);
        return m.find() && !m.group(1).contains("datetime");
    }

    /**
     * {@code text} with comments and string/char literal contents blanked to spaces, so patterns
     * never match inside them and every offset still points at the same source position.
     */
    @NotNull
    static String code(@NotNull CharSequence text) {
        StringBuilder out = new StringBuilder(text);
        int i = 0;
        int n = text.length();
        while (i < n) {
            char c = text.charAt(i);
            if (c == '/' && i + 1 < n && text.charAt(i + 1) == '/') {
                while (i < n && text.charAt(i) != '\n') {
                    out.setCharAt(i++, ' ');
                }
            } else if (c == '/' && i + 1 < n && text.charAt(i + 1) == '*') {
                while (i < n && !(text.charAt(i) == '*' && i + 1 < n && text.charAt(i + 1) == '/')) {
                    blank(out, i++);
                }
                if (i < n) {
                    out.setCharAt(i++, ' ');
                    out.setCharAt(i++, ' ');
                }
            } else if (c == '"' || c == '\'') {
                i++;
                while (i < n && text.charAt(i) != c && text.charAt(i) != '\n') {
                    if (text.charAt(i) == '\\' && i + 1 < n) {
                        out.setCharAt(i++, ' ');
                    }
                    out.setCharAt(i++, ' ');
                }
                i++;
            } else {
                i++;
            }
        }
        return out.toString();
    }

    private static void blank(@NotNull StringBuilder out, int i) {
        if (out.charAt(i) != '\n') {
            out.setCharAt(i, ' ');
        }
    }
}
