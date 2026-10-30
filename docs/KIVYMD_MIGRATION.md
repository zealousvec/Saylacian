# KivyMD migration note

## Current state

Saylacian pins KivyMD 1.2.0 in `requirements-kivy.txt` and the runtime lock. It starts and passes the current Windows UI acceptance run, but KivyMD emits its upstream deprecation warning. The live run also emits a `padding_x` deprecation from KivyMD's own label/menu KV rules; Saylacian does not set that property directly. The project has not migrated.

The same run exposed a Kivy minimum-window-size warning. This was caused by assigning width and height after the Window existed. Both values now enter Kivy's graphics config before Window initialization, and the warning disappeared in the repeated live run.

KivyMD 2.0.0 is now a released version. Its upstream changelog calls out an API break, declarative widget changes across KivyMD, and Material Design 3 support. Replacing the pin in the working application is not a safe one-line update: Saylacian imports and KV files use the 1.2.0 widget/property APIs.

## Low-risk path

1. Keep the existing pin for the published alpha and reproducible environment.
2. Create an isolated migration branch and environment; leave the approved UI and current lock untouched.
3. Inventory each KivyMD import, widget, KV property and theme setting used by `main.py` and `app/main.kv` against the 2.0.0 migration documentation.
4. Port the smallest representative screen first, preserving the current black-and-white layout and interaction.
5. Run unit tests, the live Kivy acceptance flow, keyboard/focus and resize checks, packaging smoke tests, and screenshot comparison against the approved screen.
6. Adopt the new pin only after all acceptance checks pass and the package/runtime lock is reproducible. Keep the prior pin available for rollback until that decision.

Do not install from a floating `master` branch for a release build. If a required fix exists only upstream, pin an exact commit in the isolated trial and record its hash; otherwise test the published 2.0.0 release.

## References

- [KivyMD changelog](https://kivymd.readthedocs.io/en/latest/changelog/): 2.0.0 release notes, declarative API break, and Material Design 3 changes.
- [KivyMD installation guide](https://kivymd.readthedocs.io/en/latest/getting-started/): release installation and guidance to use a commit hash when installing development source.
- [KivyMD 1.2.0 package page](https://pypi.org/project/kivymd/1.2.0/): current project pin and package metadata.

## Saylacian API exposure audit (2026-10-24)

The app still uses KivyMD 1.2.0 APIs in active UI paths. A migration is substantive and should stay isolated:

| Current API/use | 2.0 migration impact | Required proof |
|---|---|---|
| `MDFlatButton` throughout KV and Python dialogs/history | Replace with `MDButton` plus `MDButtonText`, selecting the equivalent text style. | Verify dialog layout, history row sizing, keyboard activation, focus/disabled states. |
| `MDFillRoundFlatIconButton` for source/target routes | Replace with `MDButton` and nested `MDButtonIcon`/`MDButtonText`; explicit color/style properties differ. | Screenshot compare route geometry, black/white palette, responsive layout and glyph fonts. |
| `MDDialog(title=..., text=..., buttons=...)` | 2.0 composes headline/supporting text and `MDDialogButtonContainer`; existing constructor content/buttons pattern changes. | Confirm safe KEEP default, selection, Escape, resize and dismissal behavior. |
| `MDTextField(mode="rectangle")` and plain field hints | 2.0 modes are `outlined`/`filled`; hints/helper text/icons are child components. | Verify multiline editing, paste, focus, keyboard shortcut interaction, line height and Coptic/Osmanya rendering. |
| `MDIconButton` used by `ActionIcon` | Still exists in 2.0, but has new style/state-layer properties and updated interaction behavior. Tooltip inheritance also needs compatibility testing. | Verify tooltips, focus/keyboard, custom icon colors, disabled state and hit area. |
| `MDLabel`/`MDCard`/theme setup | Core concepts remain, but properties and typography should be checked against 2.0 current docs. | Verify card surfaces, label contrast, text styles, screen sizes and screenshot fidelity. |

Official component pages include explicit 1.2.0-to-2.0.0 API comparisons for [buttons](https://kivymd.readthedocs.io/en/latest/components/button/), [text fields](https://kivymd.readthedocs.io/en/latest/components/text-fields/) and [dialogs](https://kivymd.readthedocs.io/en/latest/components/dialog/). Current docs are rolling docs (2.0.1.dev0 snapshot when checked); migration trial must pin an exact published version rather than rely on `latest` or floating `master`. The 1.2.0 `padding_x` warning came from KivyMD's own KV rule in runtime logs; source search found no Saylacian assignment of that property.

Recommendation: keep 1.2.0 lock for current alpha. Start any eventual port in a disposable clone/branch and Python environment, port one representative screen, then run full tests, live Kivy acceptance, keyboard and assistive-tech checks, resize matrix, visual comparison and packaging startup before considering adoption. No migration or dependency change was made in this audit.
