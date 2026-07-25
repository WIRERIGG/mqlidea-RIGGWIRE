/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.codeInsight.template.TemplateActionContext;
import com.intellij.codeInsight.template.TemplateContextType;
import org.jetbrains.annotations.NotNull;

import java.util.Set;

public class MQL5TemplateContextType extends TemplateContextType {

    private static final Set<String> MQL_EXTENSIONS = Set.of("mq4", "mq5", "mqh", "mql4", "mql5");

    public MQL5TemplateContextType() {
        // The 2-arg super(id, presentableName) ctor is deprecated -- plugin.xml already supplies
        // the id via <liveTemplateContext contextId="MQL5">, so only the presentable name is
        // needed here.
        super("MQL5");
    }

    @Override
    public boolean isInContext(@NotNull TemplateActionContext templateActionContext) {
        String fileName = templateActionContext.getFile().getName().toLowerCase();
        int dotIdx = fileName.lastIndexOf('.');
        if (dotIdx < 0) return false;
        String ext = fileName.substring(dotIdx + 1);
        return MQL_EXTENSIONS.contains(ext);
    }
}
