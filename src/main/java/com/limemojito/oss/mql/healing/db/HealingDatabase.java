/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.db;

import com.intellij.openapi.Disposable;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;

/**
 * SQLite-backed store for the healing pipeline. A single shared {@link Connection} is used for
 * the project's lifetime; ALL statement execution — reads and writes — is serialized on the
 * instance {@link ReentrantLock}, making every public method safe to call from concurrent
 * healing worker threads.
 */
public final class HealingDatabase implements Disposable {

    private static final Logger LOG = Logger.getInstance(HealingDatabase.class);
    private static final String DB_FILE_NAME = "mql-healing.db";

    private final Project project;
    private final ReentrantLock lock = new ReentrantLock();
    private volatile Connection connection;

    public HealingDatabase(@NotNull Project project) {
        this.project = project;
    }

    public static HealingDatabase getInstance(@NotNull Project project) {
        return project.getService(HealingDatabase.class);
    }

    public void initialize() {
        String basePath = project.getBasePath();
        if (basePath == null) return;

        Path dbPath = Path.of(basePath, ".idea", DB_FILE_NAME);
        lock.lock();
        try {
            Class.forName("org.sqlite.JDBC");
            connection = DriverManager.getConnection("jdbc:sqlite:" + dbPath);
            connection.setAutoCommit(true);
            createSchema();
            LOG.info("Healing database initialized at " + dbPath);
        } catch (Exception e) {
            LOG.warn("Failed to initialize healing database", e);
        } finally {
            lock.unlock();
        }
    }

    private void createSchema() throws SQLException {
        try (Statement stmt = connection.createStatement()) {
            stmt.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS problems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_url TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        line INTEGER NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        inspection_name TEXT NOT NULL,
                        fix_hint TEXT,
                        first_seen_at INTEGER NOT NULL,
                        last_seen_at INTEGER NOT NULL,
                        resolved_at INTEGER NOT NULL DEFAULT 0
                    )
                    """);
            stmt.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS grok_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        problem_id INTEGER NOT NULL,
                        insight TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        FOREIGN KEY (problem_id) REFERENCES problems(id)
                    )
                    """);
            stmt.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS claude_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        problem_id INTEGER NOT NULL,
                        diff TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at INTEGER NOT NULL,
                        applied_at INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY (problem_id) REFERENCES problems(id)
                    )
                    """);
            stmt.executeUpdate(
                    "CREATE INDEX IF NOT EXISTS idx_problems_file_url ON problems(file_url)");
            stmt.executeUpdate(
                    "CREATE INDEX IF NOT EXISTS idx_problems_resolved ON problems(resolved_at)");
            stmt.executeUpdate(
                    "CREATE INDEX IF NOT EXISTS idx_grok_problem ON grok_insights(problem_id)");
            stmt.executeUpdate(
                    "CREATE INDEX IF NOT EXISTS idx_claude_problem ON claude_tasks(problem_id)");
            stmt.executeUpdate(
                    "CREATE INDEX IF NOT EXISTS idx_claude_status ON claude_tasks(status)");
        }
    }

    /**
     * Sync the problems cache from MqlProblemsLoggerService into the database.
     * Upserts problems: existing ones are updated (last_seen_at), new ones are inserted,
     * problems no longer present are marked resolved.
     */
    public void syncProblems(@NotNull Map<String, List<ProblemSnapshot>> fileProblems) {
        Connection conn = connection;
        if (conn == null) return;

        lock.lock();
        try {
            conn.setAutoCommit(false);

            long now = System.currentTimeMillis();

            // Mark all unresolved problems as potentially resolved
            try (PreparedStatement markStmt = conn.prepareStatement(
                    "UPDATE problems SET resolved_at = ? WHERE resolved_at = 0")) {
                markStmt.setLong(1, now);
                markStmt.executeUpdate();
            }

            // Upsert each current problem
            try (PreparedStatement findStmt = conn.prepareStatement(
                    "SELECT id FROM problems WHERE file_url = ? AND line = ? AND inspection_name = ? AND message = ? " +
                            "ORDER BY id DESC LIMIT 1");
                 PreparedStatement updateStmt = conn.prepareStatement(
                         "UPDATE problems SET last_seen_at = ?, resolved_at = 0, message = ?, fix_hint = ?, severity = ? WHERE id = ?");
                 PreparedStatement insertStmt = conn.prepareStatement(
                         "INSERT INTO problems (file_url, file_path, line, severity, message, inspection_name, fix_hint, first_seen_at, last_seen_at) " +
                                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")) {

                for (Map.Entry<String, List<ProblemSnapshot>> entry : fileProblems.entrySet()) {
                    String fileUrl = entry.getKey();
                    for (ProblemSnapshot p : entry.getValue()) {
                        // Match any existing row for this problem — whether just marked resolved
                        // this cycle or resolved in a prior cycle — and revive it instead of
                        // inserting a duplicate row
                        findStmt.setString(1, fileUrl);
                        findStmt.setInt(2, p.line());
                        findStmt.setString(3, p.inspectionName());
                        findStmt.setString(4, p.message());
                        try (ResultSet rs = findStmt.executeQuery()) {
                            if (rs.next()) {
                                long existingId = rs.getLong(1);
                                updateStmt.setLong(1, now);
                                updateStmt.setString(2, p.message());
                                updateStmt.setString(3, p.fixHint());
                                updateStmt.setString(4, p.severity());
                                updateStmt.setLong(5, existingId);
                                updateStmt.executeUpdate();
                            } else {
                                insertStmt.setString(1, fileUrl);
                                insertStmt.setString(2, p.filePath());
                                insertStmt.setInt(3, p.line());
                                insertStmt.setString(4, p.severity());
                                insertStmt.setString(5, p.message());
                                insertStmt.setString(6, p.inspectionName());
                                insertStmt.setString(7, p.fixHint());
                                insertStmt.setLong(8, now);
                                insertStmt.setLong(9, now);
                                insertStmt.executeUpdate();
                            }
                        }
                    }
                }
            }

            conn.commit();
            conn.setAutoCommit(true);
        } catch (SQLException e) {
            LOG.warn("Failed to sync problems to healing database", e);
            try {
                conn.rollback();
                conn.setAutoCommit(true);
            } catch (SQLException ex) {
                LOG.warn("Rollback failed", ex);
            }
        } finally {
            lock.unlock();
        }
    }

    @NotNull
    public List<ProblemRecord> getUnresolvedProblems() {
        return queryProblems("SELECT * FROM problems WHERE resolved_at = 0 ORDER BY id");
    }

    @NotNull
    public List<ProblemRecord> getProblemsWithoutGrokInsight() {
        return queryProblems(
                "SELECT p.* FROM problems p LEFT JOIN grok_insights g ON p.id = g.problem_id " +
                        "WHERE p.resolved_at = 0 AND g.id IS NULL ORDER BY p.id");
    }

    @NotNull
    public List<ProblemRecord> getProblemsWithInsightButNoClaudeTask() {
        // A problem is eligible when it has no non-failed task: failed tasks must not
        // permanently block a retry.
        return queryProblems(
                "SELECT DISTINCT p.* FROM problems p " +
                        "INNER JOIN grok_insights g ON p.id = g.problem_id " +
                        "WHERE p.resolved_at = 0 AND NOT EXISTS (" +
                        "SELECT 1 FROM claude_tasks c WHERE c.problem_id = p.id AND c.status <> 'failed'" +
                        ") ORDER BY p.id");
    }

    /**
     * Problems eligible for the single combined-call Claude CLI pass: unresolved and with no
     * non-failed claude_task. Unlike {@link #getProblemsWithInsightButNoClaudeTask()} this does
     * NOT require a prior Grok insight — the CLI path analyzes and fixes in one call. Failed
     * tasks do not block eligibility, so rate-limited problems are retried on a later cycle.
     */
    @NotNull
    public List<ProblemRecord> getProblemsNeedingFix() {
        return queryProblems(
                "SELECT p.* FROM problems p " +
                        "WHERE p.resolved_at = 0 AND NOT EXISTS (" +
                        "SELECT 1 FROM claude_tasks c WHERE c.problem_id = p.id AND c.status <> 'failed'" +
                        ") ORDER BY p.id");
    }

    /**
     * Maps each problem id to its most recent non-failed Claude fix diff. Used to build the
     * auto-generated healing catalog. Problems with no usable fix are simply absent.
     */
    @NotNull
    public java.util.Map<Long, String> getLatestDiffsByProblem() {
        java.util.Map<Long, String> out = new java.util.HashMap<>();
        Connection conn = connection;
        if (conn == null) return out;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "SELECT problem_id, diff FROM claude_tasks " +
                        "WHERE status <> 'failed' AND diff IS NOT NULL AND TRIM(diff) <> '' ORDER BY id");
             ResultSet rs = stmt.executeQuery()) {
            // Ascending id → later rows overwrite earlier ones, leaving the newest diff per problem.
            while (rs.next()) {
                out.put(rs.getLong("problem_id"), rs.getString("diff"));
            }
        } catch (SQLException e) {
            LOG.warn("Failed to load diffs for healing catalog", e);
        } finally {
            lock.unlock();
        }
        return out;
    }

    public void insertGrokInsight(long problemId, @NotNull String insight) {
        Connection conn = connection;
        if (conn == null) return;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO grok_insights (problem_id, insight, created_at) VALUES (?, ?, ?)")) {
            stmt.setLong(1, problemId);
            stmt.setString(2, insight);
            stmt.setLong(3, System.currentTimeMillis());
            stmt.executeUpdate();
        } catch (SQLException e) {
            LOG.warn("Failed to insert Grok insight", e);
        } finally {
            lock.unlock();
        }
    }

    @Nullable
    public GrokInsight getGrokInsightForProblem(long problemId) {
        Connection conn = connection;
        if (conn == null) return null;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "SELECT * FROM grok_insights WHERE problem_id = ? ORDER BY created_at DESC LIMIT 1")) {
            stmt.setLong(1, problemId);
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return new GrokInsight(
                            rs.getLong("id"),
                            rs.getLong("problem_id"),
                            rs.getString("insight"),
                            rs.getLong("created_at")
                    );
                }
            }
        } catch (SQLException e) {
            LOG.warn("Failed to query Grok insight", e);
        } finally {
            lock.unlock();
        }
        return null;
    }

    public long insertClaudeTask(long problemId, @Nullable String diff, @NotNull String status) {
        Connection conn = connection;
        if (conn == null) return -1;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "INSERT INTO claude_tasks (problem_id, diff, status, created_at) VALUES (?, ?, ?, ?)",
                Statement.RETURN_GENERATED_KEYS)) {
            stmt.setLong(1, problemId);
            stmt.setString(2, diff);
            stmt.setString(3, status);
            stmt.setLong(4, System.currentTimeMillis());
            stmt.executeUpdate();
            try (ResultSet keys = stmt.getGeneratedKeys()) {
                if (keys.next()) return keys.getLong(1);
            }
        } catch (SQLException e) {
            LOG.warn("Failed to insert Claude task", e);
        } finally {
            lock.unlock();
        }
        return -1;
    }

    public void updateClaudeTaskStatus(long taskId, @NotNull String status) {
        Connection conn = connection;
        if (conn == null) return;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "UPDATE claude_tasks SET status = ? WHERE id = ?")) {
            stmt.setString(1, status);
            stmt.setLong(2, taskId);
            stmt.executeUpdate();
        } catch (SQLException e) {
            LOG.warn("Failed to update Claude task status", e);
        } finally {
            lock.unlock();
        }
    }

    public void markClaudeTaskApplied(long taskId) {
        Connection conn = connection;
        if (conn == null) return;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "UPDATE claude_tasks SET status = ?, applied_at = ? WHERE id = ?")) {
            stmt.setString(1, ClaudeTask.STATUS_APPLIED);
            stmt.setLong(2, System.currentTimeMillis());
            stmt.setLong(3, taskId);
            stmt.executeUpdate();
        } catch (SQLException e) {
            LOG.warn("Failed to mark Claude task as applied", e);
        } finally {
            lock.unlock();
        }
    }

    @NotNull
    public List<ClaudeTask> getPendingClaudeTasks() {
        return queryClaudeTasks(
                "SELECT * FROM claude_tasks WHERE status IN ('pending', 'completed') ORDER BY id");
    }

    @NotNull
    public List<ClaudeTask> getClaudeTasksForFile(@NotNull String fileUrl) {
        Connection conn = connection;
        if (conn == null) return List.of();

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "SELECT c.* FROM claude_tasks c INNER JOIN problems p ON c.problem_id = p.id " +
                        "WHERE p.file_url = ? AND c.status = ? ORDER BY c.id")) {
            stmt.setString(1, fileUrl);
            stmt.setString(2, ClaudeTask.STATUS_COMPLETED);
            try (ResultSet rs = stmt.executeQuery()) {
                return readClaudeTasks(rs);
            }
        } catch (SQLException e) {
            LOG.warn("Failed to query Claude tasks for file", e);
        } finally {
            lock.unlock();
        }
        return List.of();
    }

    @Nullable
    public ProblemRecord getProblemById(long id) {
        Connection conn = connection;
        if (conn == null) return null;

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement("SELECT * FROM problems WHERE id = ?")) {
            stmt.setLong(1, id);
            try (ResultSet rs = stmt.executeQuery()) {
                List<ProblemRecord> results = readProblems(rs);
                return results.isEmpty() ? null : results.getFirst();
            }
        } catch (SQLException e) {
            LOG.warn("Failed to query problem by id", e);
        } finally {
            lock.unlock();
        }
        return null;
    }

    public int getUnresolvedProblemCount() {
        Connection conn = connection;
        if (conn == null) return 0;

        lock.lock();
        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM problems WHERE resolved_at = 0")) {
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            LOG.warn("Failed to count unresolved problems", e);
        } finally {
            lock.unlock();
        }
        return 0;
    }

    public int getPendingClaudeTaskCount() {
        Connection conn = connection;
        if (conn == null) return 0;

        lock.lock();
        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(
                     "SELECT COUNT(*) FROM claude_tasks WHERE status IN ('pending', 'completed')")) {
            if (rs.next()) return rs.getInt(1);
        } catch (SQLException e) {
            LOG.warn("Failed to count pending Claude tasks", e);
        } finally {
            lock.unlock();
        }
        return 0;
    }

    /**
     * Counts of completed Claude tasks (with diffs, ready to apply) grouped by file URL.
     * Used to populate the {@code HealingService} pending-fix cache read by EDT consumers.
     */
    @NotNull
    public Map<String, Integer> getReadyClaudeTaskCountsByFile() {
        Connection conn = connection;
        if (conn == null) return Map.of();

        lock.lock();
        try (PreparedStatement stmt = conn.prepareStatement(
                "SELECT p.file_url, COUNT(*) FROM claude_tasks c " +
                        "INNER JOIN problems p ON c.problem_id = p.id " +
                        "WHERE c.status = ? AND c.diff IS NOT NULL GROUP BY p.file_url")) {
            stmt.setString(1, ClaudeTask.STATUS_COMPLETED);
            try (ResultSet rs = stmt.executeQuery()) {
                Map<String, Integer> counts = new HashMap<>();
                while (rs.next()) {
                    counts.put(rs.getString(1), rs.getInt(2));
                }
                return counts;
            }
        } catch (SQLException e) {
            LOG.warn("Failed to query ready Claude task counts", e);
        } finally {
            lock.unlock();
        }
        return Map.of();
    }

    @NotNull
    private List<ProblemRecord> queryProblems(@NotNull String sql) {
        Connection conn = connection;
        if (conn == null) return List.of();

        lock.lock();
        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            return readProblems(rs);
        } catch (SQLException e) {
            LOG.warn("Failed to query problems", e);
        } finally {
            lock.unlock();
        }
        return List.of();
    }

    @NotNull
    private List<ClaudeTask> queryClaudeTasks(@NotNull String sql) {
        Connection conn = connection;
        if (conn == null) return List.of();

        lock.lock();
        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            return readClaudeTasks(rs);
        } catch (SQLException e) {
            LOG.warn("Failed to query Claude tasks", e);
        } finally {
            lock.unlock();
        }
        return List.of();
    }

    @NotNull
    private static List<ProblemRecord> readProblems(@NotNull ResultSet rs) throws SQLException {
        List<ProblemRecord> results = new ArrayList<>();
        while (rs.next()) {
            results.add(new ProblemRecord(
                    rs.getLong("id"),
                    rs.getString("file_url"),
                    rs.getString("file_path"),
                    rs.getInt("line"),
                    rs.getString("severity"),
                    rs.getString("message"),
                    rs.getString("inspection_name"),
                    rs.getString("fix_hint"),
                    rs.getLong("first_seen_at"),
                    rs.getLong("last_seen_at"),
                    rs.getLong("resolved_at")
            ));
        }
        return results;
    }

    @NotNull
    private static List<ClaudeTask> readClaudeTasks(@NotNull ResultSet rs) throws SQLException {
        List<ClaudeTask> results = new ArrayList<>();
        while (rs.next()) {
            results.add(new ClaudeTask(
                    rs.getLong("id"),
                    rs.getLong("problem_id"),
                    rs.getString("diff"),
                    rs.getString("status"),
                    rs.getLong("created_at"),
                    rs.getLong("applied_at")
            ));
        }
        return results;
    }

    @Override
    public void dispose() {
        lock.lock();
        try {
            if (connection != null) {
                connection.close();
                connection = null;
            }
        } catch (SQLException e) {
            LOG.warn("Failed to close healing database", e);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Snapshot of a problem from the inspection cache, used for syncing into the DB.
     */
    public record ProblemSnapshot(
            @NotNull String filePath,
            int line,
            @NotNull String severity,
            @NotNull String message,
            @NotNull String inspectionName,
            @Nullable String fixHint
    ) {
    }
}
