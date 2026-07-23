/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ui;

import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.project.DumbAware;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.wm.ToolWindow;
import com.intellij.openapi.wm.ToolWindowFactory;
import com.intellij.ui.content.Content;
import com.intellij.ui.content.ContentFactory;
import com.intellij.ui.table.JBTable;
import com.limemojito.oss.mql.healing.HealingService;
import com.limemojito.oss.mql.healing.ai.ApiKeyStorage;
import com.limemojito.oss.mql.healing.db.ClaudeTask;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import com.limemojito.oss.mql.settings.MQL4PluginSettings;
import org.jetbrains.annotations.NotNull;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import javax.swing.table.AbstractTableModel;
import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.Font;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class HealingToolWindowFactory implements ToolWindowFactory, DumbAware {

    @Override
    public void createToolWindowContent(@NotNull Project project, @NotNull ToolWindow toolWindow) {
        // Tab 1: AI Healing tasks
        HealingPanel healingPanel = new HealingPanel(project);
        Content healingContent = ContentFactory.getInstance()
                .createContent(healingPanel, "AI Healing", false);
        toolWindow.getContentManager().addContent(healingContent);

        // Tab 2: Claude Code Sessions
        ClaudeCodePanel claudePanel = new ClaudeCodePanel(project);
        Content claudeContent = ContentFactory.getInstance()
                .createContent(claudePanel, "Claude Code", false);
        toolWindow.getContentManager().addContent(claudeContent);
    }

    // ========== Tab 1: AI Healing ==========

    private static class HealingPanel extends JPanel {

        private final Project project;
        private final HealingTaskTableModel tableModel;
        private final JLabel statusLabel;
        private final JLabel configLabel;

        HealingPanel(@NotNull Project project) {
            super(new BorderLayout());
            this.project = project;
            this.tableModel = new HealingTaskTableModel();
            this.statusLabel = new JLabel("Loading...");
            this.configLabel = new JLabel("Checking configuration...");

            JPanel topPanel = new JPanel();
            topPanel.setLayout(new BoxLayout(topPanel, BoxLayout.Y_AXIS));
            topPanel.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));

            JPanel configRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 5, 2));
            configRow.add(configLabel);
            topPanel.add(configRow);

            JPanel statusRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 5, 2));
            statusRow.add(statusLabel);
            topPanel.add(statusRow);

            JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.LEFT, 5, 2));
            JButton refreshBtn = new JButton("Refresh");
            refreshBtn.addActionListener(e -> refreshData());
            toolbar.add(refreshBtn);

            JButton healNowBtn = new JButton("Heal Now");
            healNowBtn.addActionListener(e -> {
                // healNow() runs the cycle on the service's background executor and
                // bypasses the auto-heal setting; this handler never blocks the EDT.
                HealingService.getInstance(project).healNow();
                statusLabel.setText("Manual healing cycle started...");
                healNowBtn.setEnabled(false);
                healNowBtn.setText("Healing…");
                Timer restore = new Timer(5_000, evt -> {
                    healNowBtn.setText("Heal Now");
                    healNowBtn.setEnabled(true);
                    refreshData();
                });
                restore.setRepeats(false);
                restore.start();
            });
            toolbar.add(healNowBtn);

            JButton startBtn = new JButton("Start Service");
            startBtn.addActionListener(e -> {
                HealingService.getInstance(project).start();
                statusLabel.setText("Healing service started");
                refreshData();
            });
            toolbar.add(startBtn);

            JButton stopBtn = new JButton("Stop Service");
            stopBtn.addActionListener(e -> {
                HealingService.getInstance(project).stop();
                statusLabel.setText("Healing service stopped");
            });
            toolbar.add(stopBtn);

            topPanel.add(toolbar);
            topPanel.add(Box.createVerticalStrut(5));
            add(topPanel, BorderLayout.NORTH);

            JBTable table = new JBTable(tableModel);
            table.setAutoResizeMode(JBTable.AUTO_RESIZE_ALL_COLUMNS);
            add(new JScrollPane(table), BorderLayout.CENTER);

            Timer timer = new Timer(30_000, e -> refreshData());
            timer.setRepeats(true);
            timer.start();

            refreshData();
        }

        private void refreshData() {
            ApplicationManager.getApplication().executeOnPooledThread(() -> {
                if (project.isDisposed()) return;

                MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
                boolean grokConfigured = ApiKeyStorage.getApiKey(ApiKeyStorage.GROK_KEY) != null;
                boolean claudeConfigured = ApiKeyStorage.getApiKey(ApiKeyStorage.CLAUDE_KEY) != null;
                boolean autoHeal = settings.isAutoHealEnabled();
                int delayMin = settings.getHealingDelayMinutes();

                String configStatus = "Grok: " + (grokConfigured ? "configured" : "NOT SET") +
                        " | Claude: " + (claudeConfigured ? "configured" : "NOT SET") +
                        " | Auto-heal: " + (autoHeal ? "ON" : "OFF") +
                        " | Interval: " + delayMin + "min";

                HealingDatabase db = HealingDatabase.getInstance(project);
                int problemCount = db.getUnresolvedProblemCount();
                int pendingFixes = db.getPendingClaudeTaskCount();
                String statusText = "Problems in DB: " + problemCount +
                        " | Pending AI fixes: " + pendingFixes;

                List<TaskRow> rows = new ArrayList<>();
                List<ClaudeTask> tasks = db.getPendingClaudeTasks();
                for (ClaudeTask task : tasks) {
                    ProblemRecord problem = db.getProblemById(task.problemId());
                    if (problem != null) {
                        rows.add(new TaskRow(
                                problem.filePath() + ":" + problem.line(),
                                problem.inspectionName(),
                                task.status(),
                                task.id()
                        ));
                    }
                }

                SwingUtilities.invokeLater(() -> {
                    if (project.isDisposed()) return;
                    configLabel.setText(configStatus);
                    statusLabel.setText(statusText);
                    tableModel.setRows(rows);
                });
            });
        }
    }

    // ========== Tab 2: Claude Code Sessions ==========

    private static class ClaudeCodePanel extends JPanel {

        private static final DateTimeFormatter TIME_FMT =
                DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss").withZone(ZoneId.systemDefault());

        private final Project project;
        private final SessionTableModel tableModel;
        private final JLabel statusLabel;
        private final JTextArea detailArea;

        ClaudeCodePanel(@NotNull Project project) {
            super(new BorderLayout());
            this.project = project;
            this.tableModel = new SessionTableModel();
            this.statusLabel = new JLabel("Loading sessions...");
            this.detailArea = new JTextArea(6, 60);
            detailArea.setEditable(false);
            detailArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));

            JPanel topPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 5, 2));
            JButton refreshBtn = new JButton("Refresh");
            refreshBtn.addActionListener(e -> refreshSessions());
            topPanel.add(refreshBtn);
            topPanel.add(statusLabel);
            add(topPanel, BorderLayout.NORTH);

            JBTable table = new JBTable(tableModel);
            table.setAutoResizeMode(JBTable.AUTO_RESIZE_ALL_COLUMNS);
            table.getSelectionModel().addListSelectionListener(e -> {
                if (!e.getValueIsAdjusting()) {
                    int row = table.getSelectedRow();
                    if (row >= 0 && row < tableModel.rows.size()) {
                        showSessionDetail(tableModel.rows.get(row));
                    }
                }
            });

            // Split: table on top, detail below
            JPanel centerPanel = new JPanel(new BorderLayout());
            centerPanel.add(new JScrollPane(table), BorderLayout.CENTER);
            centerPanel.add(new JScrollPane(detailArea), BorderLayout.SOUTH);
            add(centerPanel, BorderLayout.CENTER);

            Timer timer = new Timer(60_000, e -> refreshSessions());
            timer.setRepeats(true);
            timer.start();

            refreshSessions();
        }

        private void refreshSessions() {
            ApplicationManager.getApplication().executeOnPooledThread(() -> {
                if (project.isDisposed()) return;

                Path claudeDir = findClaudeProjectDir();
                if (claudeDir == null) {
                    SwingUtilities.invokeLater(() ->
                            statusLabel.setText("No Claude Code sessions found"));
                    return;
                }

                List<SessionRow> sessions = new ArrayList<>();
                try (DirectoryStream<Path> stream = Files.newDirectoryStream(claudeDir, "*.jsonl")) {
                    for (Path jsonl : stream) {
                        SessionRow row = parseSessionFile(jsonl);
                        if (row != null) sessions.add(row);
                    }
                } catch (IOException e) {
                    // ignore
                }

                sessions.sort(Comparator.comparingLong(SessionRow::lastModified).reversed());

                SwingUtilities.invokeLater(() -> {
                    if (project.isDisposed()) return;
                    statusLabel.setText(sessions.size() + " Claude Code session(s) found");
                    tableModel.setRows(sessions);
                });
            });
        }

        private SessionRow parseSessionFile(@NotNull Path jsonlPath) {
            try {
                String fileName = jsonlPath.getFileName().toString();
                String sessionId = fileName.replace(".jsonl", "");
                long lastModified = Files.getLastModifiedTime(jsonlPath).toMillis();
                long size = Files.size(jsonlPath);
                long lineCount = Files.lines(jsonlPath).count();

                // Read first user message to get slug and branch
                String slug = "";
                String branch = "";
                String model = "";
                int userMessages = 0;
                int assistantMessages = 0;

                for (String line : Files.readAllLines(jsonlPath)) {
                    if (line.contains("\"type\":\"user\"") || line.contains("\"type\": \"user\"")) {
                        userMessages++;
                        if (slug.isEmpty() && line.contains("\"slug\"")) {
                            slug = extractJsonField(line, "slug");
                        }
                        if (branch.isEmpty() && line.contains("\"gitBranch\"")) {
                            branch = extractJsonField(line, "gitBranch");
                        }
                    } else if (line.contains("\"type\":\"assistant\"") || line.contains("\"type\": \"assistant\"")) {
                        assistantMessages++;
                        if (model.isEmpty() && line.contains("\"model\"")) {
                            model = extractJsonField(line, "model");
                        }
                    }
                }

                String timeStr = TIME_FMT.format(Instant.ofEpochMilli(lastModified));
                String sizeStr = size > 1_048_576
                        ? String.format("%.1f MB", size / 1_048_576.0)
                        : String.format("%.1f KB", size / 1024.0);

                return new SessionRow(
                        sessionId,
                        slug.isEmpty() ? sessionId.substring(0, 8) : slug,
                        branch,
                        model,
                        userMessages,
                        assistantMessages,
                        sizeStr,
                        timeStr,
                        lastModified,
                        jsonlPath
                );
            } catch (IOException e) {
                return null;
            }
        }

        private void showSessionDetail(@NotNull SessionRow row) {
            ApplicationManager.getApplication().executeOnPooledThread(() -> {
                StringBuilder sb = new StringBuilder();
                sb.append("Session: ").append(row.sessionId).append("\n");
                sb.append("Slug: ").append(row.slug).append("\n");
                sb.append("Branch: ").append(row.branch).append("\n");
                sb.append("Model: ").append(row.model).append("\n");
                sb.append("Messages: ").append(row.userMsgs).append(" user, ")
                        .append(row.assistantMsgs).append(" assistant\n");
                sb.append("Size: ").append(row.size).append("\n");
                sb.append("Last Modified: ").append(row.lastModifiedStr).append("\n");
                sb.append("Path: ").append(row.path).append("\n");

                // Show last user message
                try {
                    List<String> lines = Files.readAllLines(row.path);
                    String lastUserMsg = "";
                    for (int i = lines.size() - 1; i >= 0; i--) {
                        String line = lines.get(i);
                        if (line.contains("\"type\":\"user\"") || line.contains("\"type\": \"user\"")) {
                            // Extract content
                            String content = extractJsonField(line, "content");
                            if (!content.isEmpty() && content.length() > 5) {
                                lastUserMsg = content;
                                break;
                            }
                        }
                    }
                    if (!lastUserMsg.isEmpty()) {
                        sb.append("\nLast User Message:\n");
                        String preview = lastUserMsg.length() > 500
                                ? lastUserMsg.substring(0, 500) + "..."
                                : lastUserMsg;
                        sb.append(preview);
                    }
                } catch (IOException e) {
                    sb.append("\nCould not read session file");
                }

                String detail = sb.toString();
                SwingUtilities.invokeLater(() -> detailArea.setText(detail));
            });
        }

        private Path findClaudeProjectDir() {
            String basePath = project.getBasePath();
            if (basePath == null) return null;

            // Convert project path to Claude's directory naming: C--Users-dorwi-...
            String normalized = basePath.replace("\\", "-").replace("/", "-").replace(":", "");
            if (normalized.startsWith("-")) normalized = normalized.substring(1);

            String userHome = System.getProperty("user.home");
            Path claudeProjectDir = Path.of(userHome, ".claude", "projects", normalized);
            if (Files.isDirectory(claudeProjectDir)) return claudeProjectDir;

            // Try alternative: with C- prefix
            String withDrive = basePath.replace("\\", "-").replace("/", "-");
            withDrive = withDrive.replace(":", "");
            Path altDir = Path.of(userHome, ".claude", "projects", withDrive);
            if (Files.isDirectory(altDir)) return altDir;

            // Scan all project dirs for a match
            Path projectsDir = Path.of(userHome, ".claude", "projects");
            if (!Files.isDirectory(projectsDir)) return null;

            try (DirectoryStream<Path> stream = Files.newDirectoryStream(projectsDir)) {
                for (Path dir : stream) {
                    if (Files.isDirectory(dir)) {
                        String dirName = dir.getFileName().toString();
                        if (dirName.contains(project.getName())) {
                            return dir;
                        }
                    }
                }
            } catch (IOException e) {
                // ignore
            }
            return null;
        }

        @NotNull
        private static String extractJsonField(@NotNull String json, @NotNull String field) {
            String pattern = "\"" + field + "\":\"";
            int idx = json.indexOf(pattern);
            if (idx < 0) {
                pattern = "\"" + field + "\": \"";
                idx = json.indexOf(pattern);
            }
            if (idx < 0) return "";
            int start = idx + pattern.length();
            int end = json.indexOf("\"", start);
            if (end < 0) return "";
            return json.substring(start, end);
        }
    }

    // ========== Table Models ==========

    private static class HealingTaskTableModel extends AbstractTableModel {

        private static final String[] COLUMNS = {"Location", "Inspection", "Status", "Task ID"};
        private List<TaskRow> rows = new ArrayList<>();

        void setRows(List<TaskRow> rows) {
            this.rows = rows;
            fireTableDataChanged();
        }

        @Override
        public int getRowCount() { return rows.size(); }

        @Override
        public int getColumnCount() { return COLUMNS.length; }

        @Override
        public String getColumnName(int column) { return COLUMNS[column]; }

        @Override
        public Object getValueAt(int rowIndex, int columnIndex) {
            TaskRow row = rows.get(rowIndex);
            return switch (columnIndex) {
                case 0 -> row.location;
                case 1 -> row.inspection;
                case 2 -> row.status;
                case 3 -> row.taskId;
                default -> "";
            };
        }
    }

    private static class SessionTableModel extends AbstractTableModel {

        private static final String[] COLUMNS = {"Session", "Branch", "Model", "Messages", "Size", "Last Modified"};
        private List<SessionRow> rows = new ArrayList<>();

        void setRows(List<SessionRow> rows) {
            this.rows = rows;
            fireTableDataChanged();
        }

        @Override
        public int getRowCount() { return rows.size(); }

        @Override
        public int getColumnCount() { return COLUMNS.length; }

        @Override
        public String getColumnName(int column) { return COLUMNS[column]; }

        @Override
        public Object getValueAt(int rowIndex, int columnIndex) {
            SessionRow row = rows.get(rowIndex);
            return switch (columnIndex) {
                case 0 -> row.slug;
                case 1 -> row.branch;
                case 2 -> row.model;
                case 3 -> row.userMsgs + "/" + row.assistantMsgs;
                case 4 -> row.size;
                case 5 -> row.lastModifiedStr;
                default -> "";
            };
        }
    }

    private record TaskRow(String location, String inspection, String status, long taskId) {
    }

    private record SessionRow(String sessionId, String slug, String branch, String model,
                               int userMsgs, int assistantMsgs, String size,
                               String lastModifiedStr, long lastModified, Path path) {
    }
}
