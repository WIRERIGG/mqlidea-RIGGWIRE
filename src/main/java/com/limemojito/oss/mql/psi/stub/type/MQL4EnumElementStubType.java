/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.type;

import com.intellij.lang.LighterAST;
import com.intellij.lang.LighterASTNode;
import com.intellij.lang.LighterASTTokenNode;
import com.intellij.psi.impl.source.tree.LightTreeUtil;
import com.intellij.psi.stubs.ILightStubElementType;
import com.intellij.psi.stubs.IndexSink;
import com.intellij.psi.stubs.StubElement;
import com.intellij.psi.stubs.StubInputStream;
import com.intellij.psi.stubs.StubOutputStream;
import com.intellij.util.io.StringRef;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.index.MQL4IndexKeys;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.stub.MQL4EnumElementStub;
import com.limemojito.oss.mql.psi.stub.impl.MQL4EnumElementStubImpl;
import com.limemojito.oss.mql.util.TextUtils;

import java.io.IOException;

/**
 * Light stub for an {@code ENUM_STATEMENT}. Stores the enum TYPE name (the first direct IDENTIFIER
 * child; {@code null} for an anonymous {@code enum { ... }}). Every enum node gets a stub — a
 * class-nested enum is fine because its parent (the class) is itself stubbed. The name is indexed
 * into {@link MQL4IndexKeys#ENUM_NAME_INDEX_KEY} so enum-type resolution can query the stub index
 * instead of walking the AST of every #include-closure file.
 */
public class MQL4EnumElementStubType extends ILightStubElementType<MQL4EnumElementStub, MQL4EnumElement> {

    public MQL4EnumElementStubType() {
        super("ENUM_STATEMENT", MQL4Language.INSTANCE);
    }

    @NotNull
    @Override
    public MQL4EnumElementStub createStub(@NotNull LighterAST tree, @NotNull LighterASTNode node, @NotNull StubElement parentStub) {
        // Anonymous enum: no direct IDENTIFIER child -> null name (never indexed), mirroring
        // MQL4EnumElement.getTypeName() which reads the same first direct IDENTIFIER child.
        LighterASTNode nameNode = LightTreeUtil.firstChildOfType(tree, node, MQL4Elements.IDENTIFIER);
        String name = nameNode == null ? null : ((LighterASTTokenNode) nameNode).getText().toString();
        return new MQL4EnumElementStubImpl(parentStub, name);
    }

    @Override
    public MQL4EnumElement createPsi(@NotNull MQL4EnumElementStub stub) {
        return new MQL4EnumElement(stub);
    }

    @NotNull
    @Override
    public MQL4EnumElementStub createStub(@NotNull MQL4EnumElement psi, StubElement parentStub) {
        return new MQL4EnumElementStubImpl(parentStub, psi.getTypeName());
    }

    @NotNull
    @Override
    public String getExternalId() {
        return "mqlidea.enum";
    }

    @Override
    public void serialize(@NotNull MQL4EnumElementStub stub, @NotNull StubOutputStream dataStream) throws IOException {
        dataStream.writeName(stub.getName());
    }

    @NotNull
    @Override
    public MQL4EnumElementStub deserialize(@NotNull StubInputStream dataStream, StubElement parentStub) throws IOException {
        StringRef ref = dataStream.readName();
        return new MQL4EnumElementStubImpl(parentStub, ref == null ? null : ref.getString());
    }

    @Override
    public void indexStub(@NotNull MQL4EnumElementStub stub, @NotNull IndexSink sink) {
        String name = stub.getName();
        if (name != null && !name.isEmpty()) {
            sink.occurrence(MQL4IndexKeys.ENUM_NAME_INDEX_KEY, TextUtils.unescape(name));
        }
    }
}
