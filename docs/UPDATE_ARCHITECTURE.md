# Update architecture and safety plan

## Separate app and model-pack lifecycles

Language packs are data artifacts with manifests, versions, download sizes, SHA-256 checks, atomic installation and storage management. App updates are a separate future path; installing a new source ZIP or committing code does not update an already-installed app. Current offline translation must continue to work when update checks are unavailable or skipped.

## App update proposal

1. Add one app version source, changelog and signed, versioned Windows releases only after an approved release process exists.
2. Make update checks explicit and nonblocking. Never download and run an arbitrary executable silently.
3. Verify release origin, cryptographic integrity and signing identity before offering an installer. SmartScreen/Application Control must remain enabled; investigate signing/distribution options rather than telling users to weaken security.
4. Ask before install. Keep user settings, history and packs outside replaceable app files; provide backup, rollback and interrupted-update recovery.
5. Test clean-machine install, upgrade, skipped version, corrupted download, offline launch and rollback. Do not claim an updater works before these tests pass.

## Pack update requirements

Keep app compatibility range, pack ID/version, upstream revision, licence, size, SHA-256 and source URL pinned. Download to a temporary path, verify before activation, install atomically, preserve the last usable pack until the new one passes validation, and support retry/removal/recovery. Model-pack changes must not alter app identity or silently expand telemetry/network behavior.

Storage pointers are untrusted data. Pack IDs and version IDs must be single safe path components; resolved pack and version directories must stay directly inside the configured store. Resolve every manifest-listed model file beneath its version directory before indexing, hashing or exposing it to inference. Reject path-like pointer/spec values and symlink escapes. Write activation pointers through a uniquely named, exclusive temporary file, flush it, then atomically replace the pointer so a stale temporary symlink cannot redirect the write. Keep the previous active version untouched when a new install fails.

## Current status

The project has an offline pack manager with manifest-pinned sources, SHA-256 verification, versioned installation, atomic activation, previous-version retention, cancellation and removal. Path containment rejects unsafe IDs/versions, traversal in `current.json`, and resolved model paths outside their version directory. Pointer activation uses an exclusive, unique temporary file. Regression tests cover POSIX and Windows traversal spellings. Windows denied both directory- and file-symlink creation in this session, so those two tests were explicitly skipped; do not claim symlink-runtime verification. A tested public installer, self-update system, release signing, clean-machine upgrade and app rollback are not available. No release or update setting should be enabled until those gates and owner approval are complete.
