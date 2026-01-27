/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiErrorElement;
import org.jetbrains.annotations.NotNull;
import ru.investflow.mql.MQL4FileType;
import ru.investflow.mql.MQL5FileType;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;

public class ParserTestUtils {
    public static List<Path> getFilesRecursively(File samplesDir) throws IOException {
        return Files.walk(samplesDir.toPath())
                    .filter(p -> isValidMqlFile(p.toFile()))
                    .collect(Collectors.toList());
    }

    public static PsiErrorElement findErrorElement(@NotNull PsiElement element) {
        if (element instanceof PsiErrorElement) {
            return (PsiErrorElement) element;
        }
        for (PsiElement child : element.getChildren()) {
            PsiErrorElement e = findErrorElement(child);
            if (e != null) {
                return e;
            }
        }
        return null;
    }

    public static boolean isValidMqlFile(File file) {
        String name = file.getName();
        return name.endsWith(MQL4FileType.SOURCE_FILE_EXTENSION) || name.endsWith(MQL4FileType.HEADER_FILE_EXTENSION)
                || name.endsWith(MQL5FileType.SOURCE_FILE_EXTENSION) || name.endsWith(MQL5FileType.HEADER_FILE_EXTENSION);
    }
}
