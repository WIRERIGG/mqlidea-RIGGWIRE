/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.ide.IconProvider;
import com.intellij.openapi.project.DumbAware;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.limemojito.oss.mql.inspection.MqlProblemsLoggerService;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.*;

/**
 * Provides distinct file icons for MQL4, MQL5, and header (.mqh) files.
 *
 * <p>In the no-problem case this returns exactly the same base icon each file's {@link
 * com.intellij.openapi.fileTypes.FileType#getIcon() FileType} already advertises (mq4/mql4 ->
 * mql4.svg, mq5/mql5 -> mql5.svg, mqh -> mqh.svg), so the platform's deferred repaint is a visual
 * no-op (no flash). Problem state is an OVERLAY badge on that same base icon (see
 * {@code MQL4Icons.*Problem}), never a different base icon -- the base icon never changes, so the
 * worst transition a file ever shows is base -> base+badge. Dumb-safe (a pure name/cache lookup).
 */
public class MQL4FileIconProvider extends IconProvider implements DumbAware {

    @Nullable
    @Override
    public Icon getIcon(@NotNull PsiElement element, int flags) {
        if (element instanceof PsiFile psiFile) {
            String name = psiFile.getName();
            boolean isHeader = name.endsWith(".mqh");
            boolean isMql5 = name.endsWith(".mq5") || name.endsWith(".mql5");
            boolean isMql4 = name.endsWith(".mq4") || name.endsWith(".mql4");

            if (!isHeader && !isMql5 && !isMql4) {
                return null;
            }

            boolean problem = hasProblems(psiFile);

            if (isHeader) {
                return problem ? MQL4Icons.HeaderFileProblem : MQL4Icons.HeaderFile;
            }
            if (isMql5) {
                return problem ? MQL4Icons.MQL5FileProblem : MQL4Icons.MQL5File;
            }
            // isMql4
            return problem ? MQL4Icons.FileProblem : MQL4Icons.File;
        }
        return null;
    }

    private static boolean hasProblems(@NotNull PsiFile psiFile) {
        Project project = psiFile.getProject();
        MqlProblemsLoggerService service = project.getServiceIfCreated(MqlProblemsLoggerService.class);
        if (service == null) {
            return false;
        }
        VirtualFile vf = psiFile.getVirtualFile();
        if (vf == null) {
            return false;
        }
        return service.hasProblems(vf.getUrl());
    }
}
