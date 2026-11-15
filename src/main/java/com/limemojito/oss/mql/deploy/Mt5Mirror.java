/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.deploy;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/**
 * Where MetaTrader keeps its copy of a repository's sources, by the same rules as the {@code mt5}
 * bridge's {@code sync}: {@code MQL5/Experts/<experts_subdir>} mirrors {@code <project_src>}, both
 * from the repository's {@code .claude/mt5-bridge.json}, overridden by {@code MT5_EXPERTS_SUBDIR}
 * and {@code MT5_PROJECT_SRC}. Read-only: nothing here writes either tree.
 */
public final class Mt5Mirror {

    public enum State { SAME, DIFFERENT, MISSING }

    private static final Pattern SUBDIR = Pattern.compile("\"experts_subdir\"\\s*:\\s*\"([^\"]*)\"");
    private static final Pattern SRC = Pattern.compile("\"project_src\"\\s*:\\s*\"([^\"]*)\"");

    /** The repository's source folder. */
    @NotNull
    public final Path source;
    /** MetaTrader's copy of it. */
    @NotNull
    public final Path mirror;

    Mt5Mirror(@NotNull Path source, @NotNull Path mirror) {
        this.source = source;
        this.mirror = mirror;
    }

    /**
     * The mirror for {@code file}, when it lies under a configured source folder whose MetaTrader
     * copy exists; null otherwise. Without a bridge config, the bridge's defaults apply.
     */
    @Nullable
    public static Mt5Mirror forFile(@NotNull Path file, @NotNull Path mql5, @NotNull Map<String, String> env, @Nullable Path home) {
        Path repo = repositoryOf(file);
        String subdir = null;
        String src = null;
        if (repo != null) {
            Path config = repo.resolve(".claude").resolve("mt5-bridge.json");
            if (Files.isRegularFile(config)) {
                try {
                    String json = Files.readString(config, StandardCharsets.UTF_8);
                    subdir = first(SUBDIR, json);
                    src = first(SRC, json);
                } catch (IOException ignored) {
                    // an unreadable config: fall back to the defaults, as the bridge does
                }
            }
        }
        subdir = env.getOrDefault("MT5_EXPERTS_SUBDIR", subdir != null ? subdir : "RIGGWIRE");
        String srcSetting = env.get("MT5_PROJECT_SRC") != null ? env.get("MT5_PROJECT_SRC") : src;
        Path source;
        if (srcSetting != null && !srcSetting.isEmpty()) {
            Path p = Path.of(srcSetting);
            source = p.isAbsolute() || repo == null ? p : repo.resolve(p);
        } else if (home != null) {
            source = home.resolve("CLionProjects/RIGGWIRE-EA-LIVE/RIGGWIRE-EA-LIVE");
        } else {
            return null;
        }
        source = source.normalize();
        Path mirror = mql5.resolve("Experts").resolve(subdir).normalize();
        if (!file.normalize().startsWith(source) || !Files.isDirectory(mirror)) {
            return null;
        }
        return new Mt5Mirror(source, mirror);
    }

    @Nullable
    private static String first(@NotNull Pattern pattern, @NotNull String json) {
        Matcher m = pattern.matcher(json);
        return m.find() ? m.group(1) : null;
    }

    /** The nearest folder above {@code file} holding {@code .git} (a folder or a worktree's file). */
    @Nullable
    static Path repositoryOf(@NotNull Path file) {
        for (Path dir = file.getParent(); dir != null; dir = dir.getParent()) {
            if (Files.exists(dir.resolve(".git"))) {
                return dir;
            }
        }
        return null;
    }

    /** MetaTrader's copy of {@code file} (which must be under {@link #source}). */
    @NotNull
    public Path copyOf(@NotNull Path file) {
        return mirror.resolve(source.relativize(file.normalize()).toString());
    }

    @NotNull
    public State state(@NotNull Path file) {
        Path copy = copyOf(file);
        if (!Files.isRegularFile(copy)) {
            return State.MISSING;
        }
        try {
            return Files.mismatch(file, copy) == -1 ? State.SAME : State.DIFFERENT;
        } catch (IOException e) {
            return State.MISSING;
        }
    }

    /** Every MQL source under {@link #source} whose MetaTrader copy differs or is missing, relative paths, sorted. */
    @NotNull
    public List<String> drifted() {
        List<String> out = new ArrayList<>();
        try (Stream<Path> files = Files.walk(source)) {
            files.filter(Files::isRegularFile).filter(Mt5Mirror::isSource).sorted().forEach(f -> {
                if (state(f) != State.SAME) {
                    out.add(source.relativize(f).toString());
                }
            });
        } catch (IOException | java.io.UncheckedIOException e) {
            return out;
        }
        return out;
    }

    static boolean isSource(@NotNull Path file) {
        String n = file.getFileName().toString().toLowerCase();
        return n.endsWith(".mq5") || n.endsWith(".mqh") || n.endsWith(".mq4");
    }
}
