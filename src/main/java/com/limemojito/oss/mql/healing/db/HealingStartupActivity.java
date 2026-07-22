/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.db;

import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.startup.StartupActivity;
import com.limemojito.oss.mql.healing.HealingService;
import com.limemojito.oss.mql.settings.MQL4PluginSettings;
import org.jetbrains.annotations.NotNull;

@SuppressWarnings("deprecation")
public class HealingStartupActivity implements StartupActivity.DumbAware {

    private static final Logger LOG = Logger.getInstance(HealingStartupActivity.class);

    @Override
    public void runActivity(@NotNull Project project) {
        // Initialize the healing database
        HealingDatabase.getInstance(project).initialize();

        // Start the healing service with configured models
        MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
        HealingService service = HealingService.getInstance(project);
        service.setGrokModel(settings.getGrokModel());
        service.setClaudeModel(settings.getClaudeModel());
        service.refreshPendingFixCacheAsync();

        if (settings.isAutoHealEnabled()) {
            service.start();
            LOG.info("AI Healing service started automatically");
        } else {
            LOG.info("AI Healing service initialized (auto-heal disabled — enable in Settings)");
        }
    }
}
