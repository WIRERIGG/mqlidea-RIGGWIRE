/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.actions.ConfigurationContext;
import com.intellij.execution.actions.LazyRunConfigurationProducer;
import com.intellij.execution.configurations.ConfigurationFactory;
import com.intellij.openapi.util.Ref;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.limemojito.oss.mql.deploy.Mt5DriftNotificationProvider;
import com.limemojito.oss.mql.deploy.Mt5Mirror;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.nio.file.Path;

/**
 * "Backtest X" from an EA's {@code .mq5} (one defining {@code OnTick}), when the bridge maps its
 * folder into MetaTrader: the configuration names that EA's {@code .ex5}, so it never falls back to
 * the bridge's default EA by accident.
 */
public class MqlBacktestConfigurationProducer extends LazyRunConfigurationProducer<MqlBacktestConfiguration> {

    @NotNull
    @Override
    public ConfigurationFactory getConfigurationFactory() {
        return MqlBacktestConfigurationType.getInstance().getConfigurationFactories()[0];
    }

    @Override
    protected boolean setupConfigurationFromContext(@NotNull MqlBacktestConfiguration configuration,
                                                    @NotNull ConfigurationContext context, @NotNull Ref<PsiElement> sourceElement) {
        PsiFile file = expertFile(context);
        String expert = file == null ? null : expertPath(file);
        if (expert == null) {
            return false;
        }
        configuration.expert = expert;
        configuration.setName("Backtest " + file.getName().replaceFirst("\\.mq5$", ""));
        sourceElement.set(file);
        return true;
    }

    @Override
    public boolean isConfigurationFromContext(@NotNull MqlBacktestConfiguration configuration, @NotNull ConfigurationContext context) {
        PsiFile file = expertFile(context);
        String expert = file == null ? null : expertPath(file);
        return expert != null && expert.equalsIgnoreCase(configuration.expert);
    }

    @Nullable
    private static PsiFile expertFile(@NotNull ConfigurationContext context) {
        PsiElement location = context.getPsiLocation();
        PsiFile file = location == null ? null : location.getContainingFile();
        VirtualFile vf = file == null ? null : file.getVirtualFile();
        if (vf == null || !"mq5".equalsIgnoreCase(vf.getExtension())) {
            return null;
        }
        for (MQL4FunctionElement f : com.intellij.psi.util.PsiTreeUtil.getChildrenOfTypeAsList(file, MQL4FunctionElement.class)) {
            if ("OnTick".equals(f.getName())) {
                return file;
            }
        }
        return null;
    }

    /** {@code Subdir\Path\EA.ex5} under MQL5\Experts, from the bridge's mapping; null when it doesn't map. */
    @Nullable
    static String expertPath(@NotNull PsiFile file) {
        VirtualFile vf = file.getVirtualFile();
        Path mql5 = Mt5DriftNotificationProvider.mql5Folder(file.getProject());
        if (vf == null || mql5 == null || !vf.isInLocalFileSystem()) {
            return null;
        }
        String home = System.getProperty("user.home");
        Path source = Path.of(vf.getPath());
        Mt5Mirror mirror = Mt5Mirror.forFile(source, mql5, System.getenv(), home == null ? null : Path.of(home));
        if (mirror == null) {
            return null;
        }
        Path experts = mql5.resolve("Experts");
        String relative = experts.relativize(mirror.copyOf(source)).toString().replace('/', '\\');
        return relative.replaceFirst("(?i)\\.mq5$", ".ex5");
    }
}
