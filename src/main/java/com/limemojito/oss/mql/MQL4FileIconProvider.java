/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.ide.IconProvider;
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
 * Returns gray (desaturated) icons for files that have inspection problems.
 */
public class MQL4FileIconProvider extends IconProvider {

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

            boolean gray = hasProblems(psiFile);

            if (isHeader) {
                return gray ? MQL4Icons.HeaderFileGray : MQL4Icons.HeaderFile;
            }
            if (isMql5) {
                return gray ? MQL4Icons.MQL5FileGray : MQL4Icons.MQL5File;
            }
            // isMql4
            return gray ? MQL4Icons.FileGray : MQL4Icons.File;
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
