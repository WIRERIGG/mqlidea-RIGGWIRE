/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub;

import com.intellij.lang.ASTNode;
import com.intellij.lang.LanguageParserDefinitions;
import com.intellij.lang.LighterASTNode;
import com.intellij.lang.ParserDefinition;
import com.intellij.lang.PsiBuilder;
import com.intellij.lang.PsiBuilderFactory;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.stubs.IStubElementType;
import com.intellij.psi.tree.ILightStubFileElementType;
import com.intellij.util.diff.FlyweightCapableTreeStructure;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.parser.MQL4Parser;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.stub.type.MQL4ClassElementStubType;
import com.limemojito.oss.mql.psi.stub.type.MQL4FunctionElementStubType;

public interface MQL4StubElements {

    int STUB_SCHEMA_VERSION = 20;

    ILightStubFileElementType FILE = new ILightStubFileElementType(MQL4Language.INSTANCE) {
        @Override
        public String getExternalId() {
            // Distinctive, plugin-unique id so the platform can tell this stub file element
            // type apart from other MQL4 languages (e.g. the upstream investflow plugin,
            // which uses the default "MQL4.FILE"). Avoids the "Cannot distinguish
            // StubFileElementTypes" warning.
            return "riggwire.mql.FILE";
        }

        @Override
        public String getDebugName() {
            return "RIGGWIRE MQL File";
        }

        public FlyweightCapableTreeStructure<LighterASTNode> parseContentsLight(ASTNode chameleon) {
            PsiElement psi = chameleon.getPsi();
            assert (psi != null) : ("Bad chameleon: " + chameleon);

            Project project = psi.getProject();
            PsiBuilderFactory factory = PsiBuilderFactory.getInstance();
            PsiBuilder builder = factory.createBuilder(project, chameleon);
            ParserDefinition parserDefinition = LanguageParserDefinitions.INSTANCE.forLanguage(getLanguage());
            assert (parserDefinition != null) : this;
            MQL4Parser parser = new MQL4Parser();
            return parser.parseLight(this, builder);
        }
    };

    IStubElementType<MQL4ClassElementStub, MQL4ClassElement> CLASS = new MQL4ClassElementStubType();

    IStubElementType<MQL4FunctionElementStub, MQL4FunctionElement> FUNCTION = new MQL4FunctionElementStubType(false);

    IStubElementType<MQL4FunctionElementStub, MQL4FunctionElement> FUNCTION_DECLARATION = new MQL4FunctionElementStubType(true);
}
