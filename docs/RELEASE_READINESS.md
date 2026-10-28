# Platform and release status

Saylacian is in alpha testing for Windows. The source app has not been prepared as a Store-ready package.

## Windows

The public source branch was cloned into a clean test folder with Python 3.12 and its pinned dependencies. French and Somali packs were downloaded to isolated test data and passed their size and SHA-256 checks. Translation, script-conversion, mode-switching and session-restore flows passed; the offline checks also passed with network access blocked.

No signed Windows installer or Store package is available on this branch. Windows Smart App Control blocked an earlier unsigned executable. Keep Windows security enabled; do not bypass the warning to run that build.

## Other platforms

- **Android:** no build or device test has been completed.
- **iOS:** no build or device test has been completed.
- **Website:** this source repository contains a desktop app, not a hosted translation service.

## Feature limits

Somali translation still needs fluent-speaker review. Borama and Kaddare cover selected chart entries, and Old Nubian reading covers a limited character table that needs specialist review. Modern Nubian varieties are not supported. See the [support matrix](SUPPORT_MATRIX.md) for routes and their current coverage.
