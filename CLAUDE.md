# CLAUDE.md

Wear OS watch faces in Watch Face Format v2 (declarative XML, `hasCode=false`).
Three faces (build flavors `compact`, `detailed`, `dual` of `:watchface`) share
one generator. They ship inside the `:app` watch app (`dev.stackon.sloppyshock`,
Kotlin + Wear Compose), which installs them with Watch Face Push (Wear OS 6).
See README.md for build commands and layout.

## Ground rules

- **Never edit generated files by hand**: `watchface/src/*/res/raw/watchface.xml`,
  `watchface/src/*/res/values/strings.xml`, `res/font/lcd_segments.ttf`,
  `res/drawable-nodpi/lcd_digit_*.png`. Edit `tools/gen_watchface.py` /
  `tools/gen_segment_font.py` and rerun them, then rebuild.
- Every WFF quirk below was found on real hardware; the emulator does not
  reproduce most of them. Verify on the Galaxy Watch (Samsung runtime) before
  claiming something works there.
- Bump `versionCode` in `watchface/build.gradle.kts` when resources change and
  the watch shows stale content.
- Keep release `optimization` disabled: resource shrinking strips
  `watchface.xml`, the font and the digit PNGs (they are referenced by name
  only), leaving an empty face. Check `unzip -l` of a release APK after build
  config changes.
- Releases: `.github/workflows/release.yml` builds the signed app APK for `v*`
  tags. App key from `SIGNING_*`, face key from `FACE_SIGNING_*` (Watch Face
  Push wants a separate face key); env vars / repository secrets, never commit
  a keystore.

## Watch Face Push (`:app`)

- Face packages must be `dev.stackon.sloppyshock.watchfacepush.<face>` and the
  face APK may contain only manifest + resources: `:watchface` builds with
  `isMinifyEnabled = true` (drops classes.dex) and `isShrinkResources = false`
  (keeps the face). Don't change either.
- `:watchface:validate<Face><Type>` runs Google's validator CLI
  (`validator-push-cli`) and writes `build/watchfacepush/<variant>/<face>.apk`
  + `<face>_token.txt`; the build fails on any failed check. `:app` copies them
  into its assets; `compact` becomes `default_watchface.apk`, whose token goes
  into the manifest (`DEFAULT_WATCHFACE_VALIDATION_TOKEN`) so Wear OS installs
  it together with the app.
- The validator enforces the WFF XSD strictly (the watches don't), e.g. at most
  8 `ComplicationSlot`s per face; the generator checks this. To see all schema
  errors, validate the XML against `docs.zip` inside the validator jar.
- Samsung allows **one** pushed face per app (`remainingSlotCount` 0 after the
  default face), so `Faces.use()` replaces the face in that slot.
- Debug builds accept `am start -S -n dev.stackon.sloppyshock/.MainActivity
  --es use <face>` (or `--es remove <face>`) and log the result plus the slot
  state under tag `SloppyShock`; keep the screen awake while it runs (frozen
  apps on Samsung don't execute).
- Watch Face Push needs Wear OS 6 (API 36): the Wear OS 5 emulator can't run
  `:app`; use `:watchface:installAllFaces` there.

## Samsung / WFF runtime pitfalls (Galaxy Watch4, Wear OS 6)

- `TimeText format="HH:mm"` / `"H:mm"` render nothing. Use `hh`/`h`
  (follow the 12/24h setting) and `hourFormat="24"` to force 24h.
- `TimeText` has no AM/PM token; use `[AMPM_STRING]` and `[IS_24_HOUR_MODE]`.
- `%` on negative numbers yields "Error"; use `x - floor(x / n) * n`.
- The runtime caches fonts by resource name across reinstalls; rename the font
  file if glyph changes don't show up.
- `ComplicationSlot` must be a direct child of `<Scene>`. Inside a `Group` it is
  silently dropped together with the whole group; inside a `ListOption` it is
  registered but never bound and not offered in the editor. A per-face layout
  switch is therefore impossible; layouts are separate flavors/APKs.
- Samsung clips a complication's drawing to its bounds. `BoundingArc` clips the
  ring away entirely, so ring slots use a full-screen `BoundingBox`. Smaller
  slots drawn later still get their own taps.
- `Text maxLines="2"` wraps at word boundaries only **without** `ellipsis`;
  with `ellipsis="TRUE"` the text stays on one line and is truncated.
- Providers send icons either as `MONOCHROMATIC_IMAGE` (calendar, …) or as a
  colour `SMALL_IMAGE` (Samsung media controls, weather); slot layouts draw both.
- Updating a pushed face changes nothing visible unless its `versionCode`
  is higher (the app compares versions); bump it when testing face changes.
- An empty `<ListOption/>` / `<Complication/>` may break parsing; the generator
  always puts a 1px transparent `PartDraw` in them.
- New slots on an existing install get no default provider; test defaults
  with a fresh install (uninstall first).

## Always-on (ambient) and display offload

Samsung offloads always-on to a coprocessor only if the face qualifies;
otherwise the main CPU draws ambient (works, costs more battery). Rules
(from the Samsung runtime):

- Exactly one clock visible in ambient: a single `DigitalClock` with `hh` and
  `mm` `TimeText`s using a `BitmapFont` of same-width 0-9 PNGs (no colon in the
  font), no `Localization`, no seconds, no Transform with expression, no
  rotated parent. This is the `aod_clock` group.
- Nothing visible in ambient may use second/minute/hour data sources
  (`SECOND*`, `MINUTE*`, `HOUR*`, `*_SINCE_EPOCH`, `UTC_TIMESTAMP`, …).
  Date, weekday, AM/PM, battery and complication data are fine. Elements
  hidden in ambient (`Variant mode="AMBIENT" target="alpha" value="0"`) don't count.
- The offloaded static layer is redrawn on date/battery/time-zone changes and
  at 00:00/12:00 only.

Check with logcat: `DWF:AmbientController: onDisplayOffloadStateSuccess` and
`AmbientDream: onOffloadStateChanged MCU Control` = offloaded;
`isOffloadable is false` / `[NOT_OFFLOADABLE] …` (tag `DWF:OffloadScene`) =
fallback. Screenshots are black while offloaded; ask the user to look.

If the log shows `Early exit timeout, reason=offbody` the watch thinks it is
off-wrist and turns the display off before any face draws. Not a face bug;
the user must re-seat the watch.

## Testing on the watch (adb over Wi-Fi)

- Address the watch explicitly (`adb -s <serial>`); a phone may be attached too.
- The watch is slow and drops Wi-Fi when dozing: wake it, wait several seconds
  before `screencap`, wrap commands in `timeout`, and run multi-step sequences
  as a script on the device (`nohup sh /data/local/tmp/x.sh &`), then pull results.
- Fake battery states with `dumpsys battery unplug|set level N` and always
  `dumpsys battery reset` afterwards.
- Long-press via `input swipe` does not open the editor on the Galaxy; it does
  on the emulator.

## Layout

Fonts: `lcd_segments` (0.765 em/char) for time, date and ghosts only;
complication text uses the system font (`SYNC_TO_DEVICE`). Single-line slot
text ends with `ellipsis="TRUE"`. Font files are reproducible (fixed head
timestamps).

All coordinates are in a 450×450 design space scaled about the centre by
`K = (PANEL_R - 7) / 177` (`pos()`, `sz()`, `box()`), so changing `PANEL_R`
keeps alignment. Segment-font text widths come from `seg_w()` (0.765 em per
char, 0.3 em for ':'); ghost "8" text and live text share box, size and
alignment so they overlay exactly.
