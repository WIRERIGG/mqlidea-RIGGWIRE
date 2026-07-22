/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ai;

import com.intellij.credentialStore.CredentialAttributes;
import com.intellij.credentialStore.CredentialAttributesKt;
import com.intellij.credentialStore.Credentials;
import com.intellij.ide.passwordSafe.PasswordSafe;
import com.intellij.util.SlowOperations;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public final class ApiKeyStorage {

    private static final String SERVICE_PREFIX = "MQL-Healing-";

    public static final String GROK_KEY = "grok-api-key";
    public static final String CLAUDE_KEY = "claude-api-key";

    private ApiKeyStorage() {
    }

    @Nullable
    public static String getApiKey(@NotNull String keyName) {
        CredentialAttributes attrs = createAttributes(keyName);
        Credentials credentials = SlowOperations.allowSlowOperations(
                () -> PasswordSafe.getInstance().get(attrs));
        return credentials != null ? credentials.getPasswordAsString() : null;
    }

    public static void setApiKey(@NotNull String keyName, @Nullable String value) {
        CredentialAttributes attrs = createAttributes(keyName);
        Credentials credentials = value != null ? new Credentials(keyName, value) : null;
        SlowOperations.allowSlowOperations(
                () -> PasswordSafe.getInstance().set(attrs, credentials));
    }

    @NotNull
    private static CredentialAttributes createAttributes(@NotNull String keyName) {
        return new CredentialAttributes(
                CredentialAttributesKt.generateServiceName(SERVICE_PREFIX, keyName)
        );
    }
}
