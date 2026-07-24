/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.intellij.lang.documentation.DocumentationProviderEx;
import com.intellij.lang.documentation.ExternalDocumentationHandler;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.editor.Editor;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.tree.IElementType;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.*;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4DocLookupElement;
import com.limemojito.oss.mql.settings.MQL4PluginSettings;
import com.limemojito.oss.mql.util.TextUtils;

import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * Documentation provider for MQL4 language.
 */
public class MQL4DocumentationProvider extends DocumentationProviderEx implements ExternalDocumentationHandler {

    private static final Logger log = Logger.getInstance(MQL4DocumentationProvider.class);

    public static final String DOC_NOT_FOUND = "";

    private static final Map<String, DocEntry> docEntryByText = new HashMap<>();
    private static final Map<String, DocEntry> docEntryByLink = new HashMap<>();
    private static final ClassLoader loader = MQL4DocumentationProvider.class.getClassLoader();
    private static boolean resourcesLoadedFlag;


    public MQL4DocumentationProvider() {
        ensureResourcesAreLoaded();
    }

    private static void ensureResourcesAreLoaded() {
        if (resourcesLoadedFlag) {
            return;
        }
        loadResource("mql4-constants", DocEntryType.BuiltInConstant);
        loadResource("mql4-functions", DocEntryType.BuiltInFunction);
        loadResource("mql4-keywords", DocEntryType.Keyword);
        loadResource("mql4-types", DocEntryType.BuiltInType);
        loadResource("mql4-preprocessor", DocEntryType.PreprocessorKeyword);
        resourcesLoadedFlag = true;
    }

    private static void loadResource(@NotNull String name, @NotNull DocEntryType type) {
        String resource = "mql/doc/" + name + ".json";
        try (Reader reader = new InputStreamReader(Objects.requireNonNull(loader.getResourceAsStream(resource)), UTF_8)) {
            Gson gson = new GsonBuilder().create();
            JsonArray arr = gson.fromJson(reader, JsonArray.class);
            for (int i = 0; i < arr.size(); i++) {
                JsonArray doc = arr.get(i).getAsJsonArray();
                DocEntry entry = new DocEntry(doc.get(0).getAsString(), doc.get(1).getAsString(), type);
                docEntryByLink.put(entry.link, entry);
                docEntryByText.put(entry.text, entry);
            }
        } catch (Exception e) {
            log.error("Error loading resource with docs: " + resource, e);
        }
    }

    @Nullable
    public static DocEntry getEntryByText(@NotNull String text) {
        ensureResourcesAreLoaded();
        return docEntryByText.get(text);
    }

    @NotNull
    public static Collection<DocEntry> getEntries() {
        ensureResourcesAreLoaded();
        return docEntryByText.values();
    }

    @Nullable
    @Override
    public String getQuickNavigateInfo(PsiElement element, PsiElement originalElement) {
        if (element instanceof com.limemojito.oss.mql.psi.impl.MQL4FunctionElement function) {
            String args = TextUtils.simplify(function.getSignature());
            return escape(function.getFunctionName()) + "(" + escape(args == null ? "" : args) + ")"
                    + locationSuffix(function.getContainingFile());
        }
        if (element instanceof com.limemojito.oss.mql.psi.impl.MQL4ClassElement cls) {
            return escape(cls.getClassType().name().toLowerCase() + " " + cls.getTypeName()) + locationSuffix(cls.getContainingFile());
        }
        return null;
    }

    @Nullable
    @Override
    public List<String> getUrlFor(PsiElement element, PsiElement originalElement) {
        return null;
    }

    @Nullable
    @Override
    public String generateDoc(PsiElement element, @Nullable PsiElement originalElement) {
        if (element instanceof com.limemojito.oss.mql.psi.impl.MQL4FunctionElement function) {
            return generateFunctionDoc(function);
        }
        if (element instanceof com.limemojito.oss.mql.psi.impl.MQL4ClassElement cls) {
            return generateClassDoc(cls);
        }
        String link = getLinkByElementText(element != null ? element : originalElement);
        return link == null ? null : generateDocByLink(link);
    }

    @NotNull
    private String generateDocByLink(@NotNull String link) {
        String resource = docLinkToResourcePath(link);
        if (loader.getResource(resource) == null) {
            DocEntry e = docEntryByLink.get(link);
            if (e != null) {
                log.warn("No docs found for " + link + "!");
                return "Resource not found: " + link;
            }
            return DOC_NOT_FOUND;
        }
        try (InputStream is = loader.getResourceAsStream(resource)) {
            return new Scanner(is, UTF_8).useDelimiter("\\A").next();
        } catch (Exception e) {
            log.error("Error loading resource with docs: " + link, e);
            return DOC_NOT_FOUND;
        }
    }

    /**
     * Returns file name for the given link.
     */
    @NotNull
    private String docLinkToResourcePath(@NotNull String link) {
        int anchorIdx = link.indexOf('#');
        String lang = getDocsLanguage();
        if (anchorIdx == -1) {
            return "mql/doc/" + lang + "/" + link + ".html";
        }
        return "mql/doc/" + lang + "/" + link.substring(0, anchorIdx) + ".html";
    }

    @Nullable
    private String getLinkByElementText(@Nullable PsiElement element) {
        if (element == null) {
            return null;
        }
        String text = element.getText();
        IElementType tt = element.getNode().getElementType();
        if (tt == MQL4Elements.L_ROUND_BRACKET) { // when positioned on '(' show doc for function name
            PsiElement bracketBlock = element.getParent();
            PsiElement functionNameEl = bracketBlock == null ? null : bracketBlock.getPrevSibling();
            if (functionNameEl != null) {
                text = functionNameEl.getText();
            }
        } else if (tt == MQL4Elements.WHITE_SPACE || tt == MQL4Elements.SEMICOLON) { // end of statement -> show docs for the statement itself.
            PsiElement prev = element.getPrevSibling();
            if (prev != null) {
                text = prev.getText();
            } else if (element.getParent().getNode().getElementType() == MQL4Elements.EMPTY_STATEMENT) {
                prev = element.getParent().getPrevSibling();
                if (prev != null) {
                    text = prev.getText();
                }
            }
        }
        DocEntry entry = docEntryByText.get(text);
        if (entry == null) {
            entry = docEntryByText.get("#" + text);
        }
        return entry == null ? null : entry.link;
    }

    @Override
    public PsiElement getDocumentationElementForLookupItem(PsiManager psiManager, Object object, PsiElement context) {
        return new MQL4DocLookupElement(object.toString(), context.getNode());
    }

    @Nullable
    @Override
    public PsiElement getCustomDocumentationElement(@NotNull Editor editor, @NotNull PsiFile file, @Nullable PsiElement contextElement) {
        return contextElement;
    }


    // ExternalDocumentationHandler methods

    @Override
    public boolean handleExternal(PsiElement element, PsiElement originalElement) {
        return getLinkByElementText(originalElement) != null;
    }

    @Override
    public boolean handleExternalLink(PsiManager psiManager, String link, PsiElement context) {
        return canFetchDocumentationLink(link);
    }

    @Override
    public boolean canFetchDocumentationLink(String link) {
        return docEntryByLink.containsKey(link) || loader.getResource(docLinkToResourcePath(link)) != null;
    }

    @NotNull
    @Override
    public String fetchExternalDocumentation(@NotNull String link, @Nullable PsiElement element) {
        return generateDocByLink(link);
    }

    public String getDocsLanguage() {
        return MQL4PluginSettings.getInstance().isUseEnDocs() ? "en" : "ru";
    }

    // ---- Project-symbol quick-doc (REVAMP_PLAN.md Phase 6, deliverable 5) ---------------------

    @NotNull
    private String generateFunctionDoc(@NotNull com.limemojito.oss.mql.psi.impl.MQL4FunctionElement function) {
        StringBuilder html = new StringBuilder();
        html.append("<div class='definition'><pre>");
        String args = com.limemojito.oss.mql.util.TextUtils.simplify(function.getSignature());
        html.append(escape(function.getFunctionName())).append('(').append(escape(args == null ? "" : args)).append(')');
        html.append("</pre></div>");
        appendDocCommentAndLocation(html, function, function.getContainingFile());
        return html.toString();
    }

    @NotNull
    private String generateClassDoc(@NotNull com.limemojito.oss.mql.psi.impl.MQL4ClassElement cls) {
        StringBuilder html = new StringBuilder();
        html.append("<div class='definition'><pre>");
        html.append(escape(cls.getClassType().name().toLowerCase())).append(' ').append(escape(cls.getTypeName()));
        html.append("</pre></div>");
        appendDocCommentAndLocation(html, cls, cls.getContainingFile());
        return html.toString();
    }

    private void appendDocCommentAndLocation(@NotNull StringBuilder html, @NotNull PsiElement declaration, @NotNull PsiFile containingFile) {
        String docComment = findPrecedingDocComment(declaration);
        if (docComment != null) {
            html.append("<div class='content'>").append(escape(docComment)).append("</div>");
        }
        html.append("<table class='sections'><tr><td valign='top' class='section'>Declared in:</td><td>")
                .append(escape(containingFile.getName())).append("</td></tr></table>");
    }

    @NotNull
    private String locationSuffix(@NotNull PsiFile containingFile) {
        return " — " + containingFile.getName();
    }

    /**
     * Contiguous comment lines directly above {@code declaration} (no blank-line gap), stripped
     * of comment markers -- a best-effort "doc comment" since MQL has no dedicated doc-comment
     * syntax/PSI to key off (unlike e.g. Javadoc). Returns {@code null} if there is none.
     */
    @Nullable
    private String findPrecedingDocComment(@NotNull PsiElement declaration) {
        java.util.List<PsiElement> comments = new java.util.ArrayList<>();
        PsiElement prev = declaration.getPrevSibling();
        while (prev != null) {
            if (prev instanceof PsiComment) {
                comments.add(0, prev);
                prev = prev.getPrevSibling();
            } else if (prev instanceof com.intellij.psi.PsiWhiteSpace && !prev.getText().contains("\n\n")) {
                prev = prev.getPrevSibling();
            } else {
                break;
            }
        }
        if (comments.isEmpty()) {
            return null;
        }
        StringBuilder text = new StringBuilder();
        for (PsiElement comment : comments) {
            String stripped = comment.getText()
                    .replaceFirst("^/\\*+", "")
                    .replaceFirst("\\*+/$", "")
                    .replaceFirst("^//+", "")
                    .strip();
            if (!stripped.isEmpty()) {
                if (text.length() > 0) {
                    text.append('\n');
                }
                text.append(stripped);
            }
        }
        return text.length() == 0 ? null : text.toString();
    }

    @NotNull
    private static String escape(@NotNull String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
}
