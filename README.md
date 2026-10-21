# SloppyShock

Negative-LCD digital watch faces for Wear OS, written in
[Watch Face Format](https://developer.android.com/training/wearables/wff) (WFF v2).
No app code: each face is declarative XML plus resources.

Three faces are built from one project, each its own APK:

| Face | Package | Layout |
|---|---|---|
| SloppyShock | `com.example.sloppyshock` | four small complications + one wide one |
| SloppyShock Detailed | `com.example.sloppyshock.detailed` | one large detail panel + one small slot |
| SloppyShock Dual | `com.example.sloppyshock.dual` | two detail panels side by side + one small slot |

All faces share: 7/14-segment digits with unlit "ghost" segments, day/date,
time with AM/PM and seconds, a 60-segment ring driven by a complication
(battery by default) or by seconds, a yellow ring marker complication, and
invisible tap areas over the time and date that open a provider/app of your
choice. Always-on mode is built to qualify for low-power display offload.

## Requirements

- Android SDK with platform 37 (`local.properties` → `sdk.dir`)
- JDK 25 (Gradle toolchain), Gradle wrapper included
- Python 3 with `fontTools` and `Pillow` (only to regenerate sources)
- A Wear OS 5+ device or emulator (`minSdk 35`)

## Build and install

```bash
./gradlew :watchface:assembleDebug          # all three faces
./gradlew :watchface:installAllFaces        # install all three
./gradlew :watchface:zipFaces               # build/dist/sloppyshock-watchfaces.zip
```

With several devices attached (e.g. a phone), select the watch:

```bash
ANDROID_SERIAL=<watch-serial> ./gradlew :watchface:installAllFaces
```

Single face: `./gradlew :watchface:installCompactDebug` (or `Detailed`, `Dual`).
In Android Studio pick the face in **Build Variants** (`compactDebug`, …).

Activate a face from the command line:

```bash
adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId com.example.sloppyshock
```

## Releases (GitHub Actions)

Pushing a tag `vX.Y.Z` runs `.github/workflows/release.yml`: it builds signed
release APKs of all three faces (versionName `X.Y.Z`, versionCode from the run
number) and publishes them as a GitHub Release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

One-time setup: create a release keystore (keep it and its passwords safe:
every future release must be signed with the same key, or updates won't install)

```bash
keytool -genkeypair -keystore sloppyshock-release.jks -alias sloppyshock \
  -keyalg RSA -keysize 4096 -validity 10000
```

and add these repository secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `SIGNING_KEYSTORE_BASE64` | output of `base64 -w0 sloppyshock-release.jks` |
| `SIGNING_STORE_PASSWORD` | keystore password |
| `SIGNING_KEY_ALIAS` | `sloppyshock` |
| `SIGNING_KEY_PASSWORD` | key password |

Local signed release build: set the same names as environment variables, with
`SIGNING_KEYSTORE` pointing at the `.jks` file, and run
`./gradlew :watchface:assembleRelease`. Without them release APKs are unsigned.

## Project structure

```
tools/
  gen_watchface.py       # generates every face's watchface.xml + strings.xml
  gen_segment_font.py    # generates the segment font and always-on digit PNGs
watchface/
  build.gradle.kts       # flavors compact/detailed/dual, installAllFaces, zipFaces
  src/main/              # shared: manifest, watch_face_info, font, digit PNGs
    res/font/lcd_segments.ttf          (generated)
    res/drawable-nodpi/lcd_digit_*.png (generated)
  src/<flavor>/res/
    raw/watchface.xml    # the face (generated)
    values/strings.xml   # names shown in the editor (generated)
    drawable/preview.png # picker preview (screenshot)
```

## Editing the faces

The XML is generated; edit the Python generators, never the XML.

```bash
python3 tools/gen_segment_font.py   # after changing glyphs, digit size or colour
python3 tools/gen_watchface.py      # after any layout/behaviour change
./gradlew :watchface:assembleDebug
```

Useful knobs in `tools/gen_watchface.py`: palette (`LCD`, `ACCENT`, `AOD_*`),
`PANEL_R` (panel size; the layout scales with it), `SLOTS_COMPACT` /
`SLOTS_DETAILED` / `SLOTS_DUAL` (slot positions and default providers),
`TAP_AREAS`, `RING_MODES`. If the main time size changes, the generator stops
and tells you which `DIGIT_PX` to set in `gen_segment_font.py`.

## Customizing on the watch

Long-press the face → edit. Settings: **Ring** (complication or seconds).
Complications page: the small slots, detail panels, the ring and the ring
marker (full-screen slots), and the **Tap on time** / **Tap on date** areas.
