#!/bin/zsh
# Publishes the built plugin to a local plugin repository that CLion/IDEA can check for updates.
# Add file://$HOME/.mqlidea-repo/updatePlugins.xml under Settings → Plugins → ⚙ → Manage Plugin Repositories.
# Usage: tools/publish-local-repo.sh   (after ./gradlew buildPlugin)
set -eu
cd "${0:A:h}/.."
REPO="${MQLIDEA_REPO:-$HOME/.mqlidea-repo}"
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' build.gradle.kts)
SINCE=$(sed -n 's/.*<idea-version since-build="\([^"]*\)".*/\1/p' src/main/resources/META-INF/plugin.xml)
ZIP="build/distributions/mqlidea-$VERSION.zip"
[[ -f "$ZIP" ]] || { echo "missing $ZIP - run ./gradlew buildPlugin first" >&2; exit 1; }
mkdir -p "$REPO"
cp "$ZIP" "$REPO/mqlidea-$VERSION.zip.new" && mv "$REPO/mqlidea-$VERSION.zip.new" "$REPO/mqlidea-$VERSION.zip"
cat > "$REPO/updatePlugins.xml.new" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<plugins>
  <plugin id="io.riggwire.mql" url="file://$REPO/mqlidea-$VERSION.zip" version="$VERSION">
    <idea-version since-build="$SINCE"/>
    <name>RIGGWIRE MQL</name>
    <vendor>RIGGWIRE Trading Systems</vendor>
    <description>MQL4/MQL5 language support for MetaTrader development.</description>
  </plugin>
</plugins>
XML
mv "$REPO/updatePlugins.xml.new" "$REPO/updatePlugins.xml"
# keep the three newest builds
ls -t "$REPO"/mqlidea-*.zip | tail -n +4 | xargs rm -f
echo "published $VERSION -> $REPO/updatePlugins.xml"
