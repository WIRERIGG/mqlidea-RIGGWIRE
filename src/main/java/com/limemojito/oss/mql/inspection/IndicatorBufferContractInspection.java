/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.search.FileTypeIndex;
import com.intellij.psi.search.FilenameIndex;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.MQL5FileType;
import com.limemojito.oss.mql.MqlHeaderFileType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * The contract between an indicator and the programs that read it, from literal values only.
 * <p>
 * In the indicator: a {@code SetIndexBuffer} index at or past {@code indicator_buffers}, plots
 * that need more buffers than are declared, and an {@code INDICATOR_DATA} buffer past the ones the
 * plots consume (MetaTrader doesn't bind it: another program's {@code CopyBuffer} gets -1, error
 * 4806, while an {@code INDICATOR_CALCULATIONS} buffer there reads fine).
 * <p>
 * In a reader: {@code CopyBuffer(h, i, ...)} where {@code h} is only ever assigned
 * {@code iCustom(.., "Name", ..)} and {@code Name.mq5} is in the project, with {@code i} a literal
 * or a {@code #define} of one: a buffer the indicator doesn't have, never binds, or binds
 * unreadably. And an {@code iCustom} passing more parameters than the indicator has inputs.
 */
public class IndicatorBufferContractInspection extends MQL5SafetyInspectionBase {

    private static final Pattern ASSIGNED_ICUSTOM = Pattern.compile(
            "\\b(\\w+)\\s*(?:\\[[^\\]]*\\]\\s*)?=\\s*iCustom\\s*\\(");
    private static final Pattern ICUSTOM = Pattern.compile("\\biCustom\\s*\\(");
    private static final Pattern COPY_BUFFER = Pattern.compile("\\bCopyBuffer\\s*\\(");
    private static final Pattern INT_DEFINE = Pattern.compile("(?m)^[ \\t]*#define[ \\t]+(\\w+)[ \\t]+(\\d+)[ \\t]*$");
    private static final Pattern PLOTS_PROPERTY = Pattern.compile("#property\\s+indicator_plots\\b");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) {
            return ProblemDescriptor.EMPTY_ARRAY;
        }
        List<ProblemDescriptor> problems = new SmartList<>();
        String code = IndicatorContract.code(file.getViewProvider().getContents());
        IndicatorContract own = IndicatorContract.of(file);
        if (own != null) {
            checkIndicator(file, code, own, manager, isOnTheFly, problems);
        }
        if (code.contains("CopyBuffer") || code.contains("iCustom")) {
            checkReader(file, code, manager, isOnTheFly, problems);
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private void checkIndicator(@NotNull PsiFile file, @NotNull String code, @NotNull IndicatorContract c,
                                @NotNull InspectionManager manager, boolean onTheFly, @NotNull List<ProblemDescriptor> out) {
        if (c.buffers >= 0 && c.plotBuffers > c.buffers) {
            Matcher m = PLOTS_PROPERTY.matcher(code);
            if (m.find()) {
                report(file, m.start(), "The " + c.plots + " plots draw from " + c.plotBuffers
                        + " buffers but indicator_buffers is " + c.buffers, manager, onTheFly, out);
            }
        }
        for (IndicatorContract.Binding b : c.bindings) {
            ProgressManager.checkCanceled();
            if (c.buffers >= 0 && b.index() >= c.buffers) {
                report(file, b.offset(), "Buffer " + b.index() + " is past indicator_buffers " + c.buffers
                        + ": SetIndexBuffer fails and the buffer never fills", manager, onTheFly, out);
            } else if (unreadable(c, b)) {
                report(file, b.offset(), unreadableMessage(b.index(), c.plotBuffers) + " here", manager, onTheFly, out);
            }
        }
    }

    private static boolean unreadable(@NotNull IndicatorContract c, @NotNull IndicatorContract.Binding b) {
        return "INDICATOR_DATA".equals(b.type()) && c.plotBuffers >= 0 && b.index() >= c.plotBuffers;
    }

    @NotNull
    private static String unreadableMessage(int index, int plotBuffers) {
        return "INDICATOR_DATA buffer " + index + " is past the " + plotBuffers
                + " buffers the plots use, so another program's CopyBuffer returns -1 (error 4806); bind it as INDICATOR_CALCULATIONS";
    }

    private void checkReader(@NotNull PsiFile file, @NotNull String code, @NotNull InspectionManager manager,
                             boolean onTheFly, @NotNull List<ProblemDescriptor> out) {
        Project project = file.getProject();
        ProjectFacts facts = ProjectFacts.of(project);
        Matcher icustom = ICUSTOM.matcher(code);
        while (icustom.find()) {
            ProgressManager.checkCanceled();
            List<int[]> args = arguments(code, icustom.end() - 1);
            if (args == null || args.size() < 3) {
                continue;
            }
            String name = literalText(file.getViewProvider().getContents(), code, args.get(2));
            IndicatorContract target = name == null ? null : contractFor(file, name);
            if (target == null || target.inputs < 0) {
                continue;
            }
            int passed = args.size() - 3;
            int accepted = target.inputs + (target.shortOnCalculate ? 1 : 0);
            if (passed > accepted) {
                report(file, args.get(2)[0], baseName(name) + " has " + target.inputs + " inputs"
                        + (target.shortOnCalculate ? " (plus the applied price)" : "") + " but iCustom passes "
                        + passed + " parameters", manager, onTheFly, out);
            }
        }
        Matcher copy = COPY_BUFFER.matcher(code);
        while (copy.find()) {
            ProgressManager.checkCanceled();
            List<int[]> args = arguments(code, copy.end() - 1);
            if (args == null || args.size() < 2) {
                continue;
            }
            String handle = text(code, args.get(0)).replaceAll("\\s*\\[.*$", "");
            String indicator = facts.indicatorOf.get(handle);
            IndicatorContract target = indicator == null ? null : contractFor(file, indicator);
            if (target == null) {
                continue;
            }
            Integer index = intValue(text(code, args.get(1)), facts.defines);
            if (index == null) {
                continue;
            }
            String label = baseName(indicator);
            int at = args.get(1)[0];
            if (target.buffers >= 0 && index >= target.buffers) {
                report(file, at, label + " declares " + target.buffers + " buffers (0-" + (target.buffers - 1)
                        + "): buffer " + index + " doesn't exist and CopyBuffer returns -1", manager, onTheFly, out);
                continue;
            }
            IndicatorContract.Binding binding = target.binding(index);
            if (binding == null) {
                if (!target.dynamicBindings && !target.bindings.isEmpty()) {
                    report(file, at, label + " never binds buffer " + index + " with SetIndexBuffer", manager, onTheFly, out);
                }
            } else if (unreadable(target, binding)) {
                report(file, at, label + "'s " + unreadableMessage(index, target.plotBuffers), manager, onTheFly, out);
            }
        }
    }

    private void report(@NotNull PsiFile file, int offset, @NotNull String message, @NotNull InspectionManager manager,
                        boolean onTheFly, @NotNull List<ProblemDescriptor> out) {
        PsiElement element = file.findElementAt(offset);
        if (element != null) {
            out.add(createWarning(manager, element, message, onTheFly));
        }
    }

    /**
     * The project's {@code Name.mq5} for an iCustom name ({@code "Folder\\Name"}, {@code "Name.ex5"}):
     * the copy sharing the longest folder path with {@code reader} (a backup folder holding another
     * copy doesn't hide it), or null when none exists or two are equally near.
     */
    @Nullable
    private static IndicatorContract contractFor(@NotNull PsiFile reader, @NotNull String indicator) {
        Project project = reader.getProject();
        Collection<VirtualFile> files = FilenameIndex.getVirtualFilesByName(baseName(indicator) + ".mq5",
                GlobalSearchScope.projectScope(project));
        VirtualFile from = reader.getOriginalFile().getVirtualFile();
        String readerPath = from == null ? "" : from.getPath();
        VirtualFile best = null;
        int bestShared = -1;
        boolean tie = false;
        for (VirtualFile candidate : files) {
            int shared = sharedFolderDepth(readerPath, candidate.getPath());
            if (shared > bestShared) {
                best = candidate;
                bestShared = shared;
                tie = false;
            } else if (shared == bestShared) {
                tie = true;
            }
        }
        if (best == null || tie) {
            return null;
        }
        PsiFile psi = PsiManager.getInstance(project).findFile(best);
        return psi == null ? null : IndicatorContract.of(psi);
    }

    private static int sharedFolderDepth(@NotNull String a, @NotNull String b) {
        String[] x = a.split("/");
        String[] y = b.split("/");
        int depth = 0;
        while (depth < x.length - 1 && depth < y.length - 1 && x[depth].equals(y[depth])) {
            depth++;
        }
        return depth;
    }

    @NotNull
    private static String baseName(@NotNull String indicator) {
        String name = indicator.replace('/', '\\');
        name = name.substring(name.lastIndexOf('\\') + 1);
        return name.endsWith(".ex5") ? name.substring(0, name.length() - 4) : name;
    }

    @Nullable
    private static Integer intValue(@NotNull String expression, @NotNull Map<String, Integer> defines) {
        String e = expression.trim();
        if (e.matches("\\d+")) {
            return Integer.parseInt(e);
        }
        return defines.get(e);
    }

    @NotNull
    private static String text(@NotNull String code, int[] range) {
        return code.substring(range[0], range[1]);
    }

    /** Argument ranges of the call whose {@code (} is at {@code open}, split on top-level commas; null if unbalanced. */
    @Nullable
    static List<int[]> arguments(@NotNull String code, int open) {
        List<int[]> args = new ArrayList<>();
        int depth = 0;
        int start = open + 1;
        for (int i = open; i < code.length(); i++) {
            char ch = code.charAt(i);
            if (ch == '(' || ch == '[' || ch == '{') {
                depth++;
            } else if (ch == ')' || ch == ']' || ch == '}') {
                depth--;
                if (depth == 0) {
                    if (!code.substring(start, i).isBlank() || !args.isEmpty()) {
                        args.add(new int[]{start, i});
                    }
                    return args;
                }
            } else if (ch == ',' && depth == 1) {
                args.add(new int[]{start, i});
                start = i + 1;
            } else if (ch == ';' && depth == 1) {
                return null;
            }
        }
        return null;
    }

    /** Facts gathered over every project MQL5 source: handle variables bound to one indicator, and integer #defines. */
    private static final class ProjectFacts {
        final Map<String, String> indicatorOf;
        final Map<String, Integer> defines;

        private ProjectFacts(Map<String, String> indicatorOf, Map<String, Integer> defines) {
            this.indicatorOf = indicatorOf;
            this.defines = defines;
        }

        static ProjectFacts of(@NotNull Project project) {
            return CachedValuesManager.getManager(project).getCachedValue(project, () ->
                    CachedValueProvider.Result.create(collect(project), PsiModificationTracker.MODIFICATION_COUNT));
        }

        private static ProjectFacts collect(@NotNull Project project) {
            Map<String, String> indicatorOf = new HashMap<>();
            Set<String> ambiguousHandles = new HashSet<>();
            Map<String, Integer> defines = new HashMap<>();
            Set<String> ambiguousDefines = new HashSet<>();
            GlobalSearchScope scope = GlobalSearchScope.projectScope(project);
            List<VirtualFile> files = new ArrayList<>(FileTypeIndex.getFiles(MQL5FileType.INSTANCE, scope));
            files.addAll(FileTypeIndex.getFiles(MqlHeaderFileType.INSTANCE, scope));
            PsiManager psi = PsiManager.getInstance(project);
            for (VirtualFile vf : files) {
                ProgressManager.checkCanceled();
                PsiFile f = psi.findFile(vf);
                if (f == null) {
                    continue;
                }
                CharSequence source = f.getViewProvider().getContents();
                String code = IndicatorContract.code(source);
                Matcher m = ASSIGNED_ICUSTOM.matcher(code);
                while (m.find()) {
                    String handle = m.group(1);
                    List<int[]> args = arguments(code, m.end() - 1);
                    String name = args != null && args.size() >= 3 ? literalText(source, code, args.get(2)) : null;
                    String previous = name == null ? null : indicatorOf.putIfAbsent(handle, name);
                    if (name == null || previous != null && !previous.equals(name)) {
                        ambiguousHandles.add(handle);
                    }
                }
                Matcher d = INT_DEFINE.matcher(code);
                while (d.find()) {
                    Integer value = Integer.parseInt(d.group(2));
                    Integer previous = defines.putIfAbsent(d.group(1), value);
                    if (previous != null && !previous.equals(value)) {
                        ambiguousDefines.add(d.group(1));
                    }
                }
            }
            ambiguousHandles.forEach(indicatorOf::remove);
            ambiguousDefines.forEach(defines::remove);
            return new ProjectFacts(indicatorOf, defines);
        }
    }

    /** The contents of a plain string literal argument, read from the unblanked source; null for anything else. */
    @Nullable
    private static String literalText(@NotNull CharSequence source, @NotNull String code, int[] range) {
        String blanked = text(code, range);
        int open = blanked.indexOf('"');
        int close = blanked.lastIndexOf('"');
        if (open < 0 || close <= open || !blanked.substring(0, open).isBlank() || !blanked.substring(close + 1).isBlank()) {
            return null;
        }
        String value = source.subSequence(range[0] + open + 1, range[0] + close).toString();
        return value.contains("\"") ? null : value.replace("\\\\", "\\");
    }
}
