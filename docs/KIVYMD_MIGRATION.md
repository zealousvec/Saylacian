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
