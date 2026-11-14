/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.type;

import com.intellij.lang.LighterAST;
import com.intellij.lang.LighterASTNode;
import com.intellij.lang.LighterASTTokenNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNamedElement;
import com.intellij.psi.impl.source.tree.LightTreeUtil;
import com.intellij.psi.stubs.ILightStubElementType;
import com.intellij.psi.stubs.IndexSink;
import com.intellij.psi.stubs.StubElement;
import com.intellij.psi.stubs.StubIndexKey;
import com.intellij.psi.stubs.StubInputStream;
import com.intellij.psi.stubs.StubOutputStream;
import com.intellij.util.io.StringRef;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.stub.MQL4NamedElementStub;
import com.limemojito.oss.mql.psi.stub.impl.MQL4NamedElementStubImpl;
import com.limemojito.oss.mql.util.TextUtils;

import java.io.IOException;
import java.util.function.Function;

/**
 * Light stub type for a declaration identified by its first direct IDENTIFIER child (a
 * {@code typedef} or a {@code #define}); the name is indexed under {@code indexKey}.
 */
public class MQL4NamedElementStubType<T extends PsiNamedElement>
        extends ILightStubElementType<MQL4NamedElementStub<T>, T> {

    @NotNull
    private final String externalId;
    @NotNull
    private final StubIndexKey<String, T> indexKey;
    @NotNull
    private final Function<MQL4NamedElementStub<T>, T> psiFactory;

    public MQL4NamedElementStubType(@NotNull String debugName, @NotNull String externalId,
                                    @NotNull StubIndexKey<String, T> indexKey,
                                    @NotNull Function<MQL4NamedElementStub<T>, T> psiFactory) {
        super(debugName, MQL4Language.INSTANCE);
        this.externalId = externalId;
        this.indexKey = indexKey;
        this.psiFactory = psiFactory;
    }

    @NotNull
    @Override
    public MQL4NamedElementStub<T> createStub(@NotNull LighterAST tree, @NotNull LighterASTNode node, @NotNull StubElement<?> parentStub) {
        LighterASTNode nameNode = LightTreeUtil.firstChildOfType(tree, node, MQL4Elements.IDENTIFIER);
        String name = nameNode == null ? null : ((LighterASTTokenNode) nameNode).getText().toString();
        return new MQL4NamedElementStubImpl<>(parentStub, this, name);
    }

    @NotNull
    @Override
    public MQL4NamedElementStub<T> createStub(@NotNull T psi, StubElement<? extends PsiElement> parentStub) {
        return new MQL4NamedElementStubImpl<>(parentStub, this, psi.getName());
    }

    @Override
    public T createPsi(@NotNull MQL4NamedElementStub<T> stub) {
        return psiFactory.apply(stub);
    }

    @NotNull
    @Override
    public String getExternalId() {
        return externalId;
    }

    @Override
    public void serialize(@NotNull MQL4NamedElementStub<T> stub, @NotNull StubOutputStream dataStream) throws IOException {
        dataStream.writeName(stub.getName());
    }

    @NotNull
    @Override
    public MQL4NamedElementStub<T> deserialize(@NotNull StubInputStream dataStream, StubElement parentStub) throws IOException {
        StringRef ref = dataStream.readName();
        return new MQL4NamedElementStubImpl<>(parentStub, this, ref == null ? null : ref.getString());
    }

    @Override
    public void indexStub(@NotNull MQL4NamedElementStub<T> stub, @NotNull IndexSink sink) {
        String name = stub.getName();
        if (name != null && !name.isEmpty()) {
            sink.occurrence(indexKey, TextUtils.unescape(name));
        }
    }
}
