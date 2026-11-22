# Clash Meta for Android Stable Builds

Download the APK for your phone from the [latest Android release](https://github.com/vertno/ClashMetaForAndroid/releases/latest). Most current Android phones use the `arm64-v8a` package. In the app, Help opens this project. Install a newer APK over your existing personal build to keep its settings.

The personal package uses `com.github.vertno.clash.meta` and its own signing certificate. It can coexist with the official app. Each release pins the source of the custom Mihomo core before building the Android libraries. [Official CMFA](https://github.com/MetaCubeX/ClashMetaForAndroid) · [Personal core releases](https://github.com/vertno/mihomo/releases)

The release tag contains the patched source and its dependency record. The `distribution` branch holds the patch and release workflow.

Each official stable tag produces one release named `vX.Y.Z-patched`. The build waits for its published custom Mihomo dependency. Later core releases do not rebuild this application.
