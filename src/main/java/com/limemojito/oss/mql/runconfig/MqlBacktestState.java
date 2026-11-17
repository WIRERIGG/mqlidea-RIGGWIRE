/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.ExecutionException;
import com.intellij.execution.configurations.CommandLineState;
import com.intellij.execution.configurations.GeneralCommandLine;
import com.intellij.execution.process.ColoredProcessHandler;
import com.intellij.execution.process.ProcessEvent;
import com.intellij.execution.process.ProcessHandler;
import com.intellij.execution.process.ProcessListener;
import com.intellij.execution.process.ProcessTerminatedListener;
import com.intellij.execution.runners.ExecutionEnvironment;
import com.intellij.ide.BrowserUtil;
import com.intellij.notification.NotificationAction;
import com.intellij.notification.NotificationGroupManager;
import com.intellij.notification.NotificationType;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.Key;
import com.limemojito.oss.mql.compiler.Mt5CliLauncher;
import com.limemojito.oss.mql.compiler.StrategyTester;
import com.limemojito.oss.mql.tester.TesterInputs;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Starts {@code mt5 backtest} for a {@link MqlBacktestConfiguration}. Refuses while MetaTrader or a
 * tester agent runs (a backtest needs the terminal to itself, and the plugin never stops it), and
 * offers the report the bridge names when it finishes. Stopping the run stops the bridge script;
 * MetaTrader finishes the test and closes itself.
 */
final class MqlBacktestState extends CommandLineState {

    static final Pattern REPORT = Pattern.compile("^\\s*Report:\\s+(.+\\.html?)\\s*$", Pattern.MULTILINE);

    private final MqlBacktestConfiguration config;

    MqlBacktestState(@NotNull MqlBacktestConfiguration config, @NotNull ExecutionEnvironment environment) {
        super(environment);
        this.config = config;
    }

    @NotNull
    @Override
    protected ProcessHandler startProcess() throws ExecutionException {
        String mt5 = Mt5CliLauncher.findMt5();
        if (mt5 == null) {
            throw new ExecutionException("The mt5 bridge isn't installed at ~/.local/bin/mt5");
        }
        StrategyTester.refreshNow();
        if (!StrategyTester.isKnown()) {
            throw new ExecutionException("Couldn't read the process table to check whether MetaTrader 5 is running, "
                    + "so the backtest wasn't started.");
        }
        if (StrategyTester.isTerminalBusy()) {
            throw new ExecutionException("MetaTrader 5 is running. A backtest needs the terminal to itself; close MetaTrader "
                    + "(or wait for the running test to finish) and run again. The plugin never stops it for you.");
        }
        GeneralCommandLine cmd = new GeneralCommandLine(MqlBacktestCommand.arguments(mt5, config.symbol, config.from,
                config.to, config.model, config.timeout))
                .withParentEnvironmentType(GeneralCommandLine.ParentEnvironmentType.CONSOLE)
                .withEnvironment(MqlBacktestCommand.environment(config.expert, config.period, config.deposit, inputsFile()));
        String base = config.getProject().getBasePath();
        if (base != null) {
            cmd.withWorkDirectory(base); // the bridge reads this repository's .claude/mt5-bridge.json
        }
        ColoredProcessHandler handler = new ColoredProcessHandler(cmd);
        AtomicReference<String> report = new AtomicReference<>();
        handler.addProcessListener(new ProcessListener() {
            @Override
            public void onTextAvailable(@NotNull ProcessEvent event, @NotNull Key outputType) {
                Matcher m = REPORT.matcher(event.getText());
                if (m.find()) {
                    report.set(m.group(1).trim());
                }
            }

            @Override
            public void processTerminated(@NotNull ProcessEvent event) {
                notifyFinished(config.getProject(), config.getName(), event.getExitCode(), report.get());
            }
        });
        ProcessTerminatedListener.attach(handler, config.getProject());
        return handler;
    }

    /** The inputs as a UTF-8 {@code Name=Value} temp file the bridge appends to {@code [TesterInputs]}, or null. */
    @Nullable
    private String inputsFile() throws ExecutionException {
        if (config.inputsFile.isEmpty()) {
            return null;
        }
        try {
            String section = TesterInputs.testerSection(TesterInputs.decode(Files.readAllBytes(Path.of(config.inputsFile))));
            File temp = Files.createTempFile("mql-backtest-inputs", ".txt").toFile();
            temp.deleteOnExit();
            Files.writeString(temp.toPath(), section, StandardCharsets.UTF_8);
            return temp.getAbsolutePath();
        } catch (IOException e) {
            throw new ExecutionException("Can't read the inputs file " + config.inputsFile + ": " + e.getMessage(), e);
        }
    }

    /** What exit codes mean, from the bridge's own script. */
    @NotNull
    static String exitMeaning(int code) {
        return switch (code) {
            case 0 -> "finished";
            case 1 -> "finished without a report (no trades, or no tester data for the symbol and dates)";
            case 2 -> "wasn't set up (the bridge's configuration or arguments were rejected)";
            case 3 -> "timed out";
            case 4 -> "rejected its arguments";
            case 5 -> "didn't start: MetaTrader 5 was already running";
            case 6 -> "gave up waiting for another backtest to finish";
            default -> "failed (exit " + code + ")";
        };
    }

    private static void notifyFinished(@NotNull Project project, @NotNull String name, int exitCode, @Nullable String report) {
        boolean ok = exitCode == 0 && report != null;
        var notification = NotificationGroupManager.getInstance().getNotificationGroup("MQL Backtest")
                .createNotification("Backtest '" + name + "' " + exitMeaning(exitCode),
                        report == null ? "" : report, ok ? NotificationType.INFORMATION : NotificationType.WARNING);
        if (report != null && new File(report).isFile()) {
            notification.addAction(NotificationAction.createSimpleExpiring("Open report", () -> BrowserUtil.browse(new File(report).toURI())));
        }
        notification.notify(project);
    }
}
