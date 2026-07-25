
/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.actions.ConfigurationContext;
import com.intellij.execution.actions.RunConfigurationProducer;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.Ref;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Set;

/**
 * Backs the run-gutter (&#9654;) on {@code OnInit}/{@code OnStart}: when invoked from a compilable
 * MQL program ({@code .mq4}/{@code .mql4}/{@code .mq5}/{@code .mql5}, never a {@code .mqh} header,
 * which cannot be built standalone) it creates/matches an {@link MQL4RunCompilerConfiguration}
 * whose {@code fileToCompile} points at that file, so the gutter action has a config to run.
 */
public class MQL4RunCompilerConfigurationProducer extends RunConfigurationProducer<MQL4RunCompilerConfiguration> {

    /** Program extensions MetaEditor can compile standalone -- headers (.mqh) are deliberately excluded. */
    private static final Set<String> COMPILABLE_PROGRAM_EXTENSIONS = Set.of("mq4", "mql4", "mq5", "mql5");

    protected MQL4RunCompilerConfigurationProducer() {
        super(MQL4RunCompilerConfigurationType.getInstance());
    }

    @Override
    protected boolean setupConfigurationFromContext(@NotNull MQL4RunCompilerConfiguration configuration,
                                                    @NotNull ConfigurationContext context,
                                                    @NotNull Ref<PsiElement> sourceElement) {
        PsiFile file = contextProgramFile(context);
        if (file == null) {
            return false;
        }
        VirtualFile vf = file.getVirtualFile();
        String storedPath = storedPath(file.getProject(), vf);
        configuration.fileToCompile = storedPath;
        configuration.setName(vf.getName());
        sourceElement.set(file);
        return true;
    }

    @Override
    public boolean isConfigurationFromContext(@NotNull MQL4RunCompilerConfiguration configuration,
                                              @NotNull ConfigurationContext context) {
        PsiFile file = contextProgramFile(context);
        if (file == null) {
            return false;
        }
        VirtualFile vf = file.getVirtualFile();
        return storedPath(file.getProject(), vf).equals(configuration.fileToCompile);
    }

    /**
     * The context's PSI file when it is a compilable MQL program (not a header), else {@code null}.
     */
    @Nullable
    private static PsiFile contextProgramFile(@NotNull ConfigurationContext context) {
        PsiElement location = context.getPsiLocation();
        if (location == null) {
            return null;
        }
        PsiFile file = location.getContainingFile();
        if (file == null) {
            return null;
        }
        VirtualFile vf = file.getVirtualFile();
        if (vf == null) {
            return null;
        }
        String ext = vf.getExtension();
        if (ext == null || !COMPILABLE_PROGRAM_EXTENSIONS.contains(ext.toLowerCase())) {
            return null;
        }
        return file;
    }

    /**
     * The path stored in {@code fileToCompile}, mirroring the run-config editor's file selector:
     * project-relative when the file lives under the project base, otherwise the absolute path.
     */
    @NotNull
    private static String storedPath(@NotNull Project project, @NotNull VirtualFile vf) {
        String basePath = project.getBasePath();
        String path = vf.getPath();
        if (basePath != null && path.startsWith(basePath)) {
            String rel = path.substring(basePath.length());
            if (rel.startsWith("/")) {
                rel = rel.substring(1);
            }
            return rel;
        }
        return path;
    }
}
