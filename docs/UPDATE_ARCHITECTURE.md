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

## Current status

The project has an offline pack manager and tests for integrity, installation and path alias behavior. A tested public installer, self-update system, release signing, clean-machine upgrade and rollback are not available. No release or update setting should be enabled until those gates and owner approval are complete.
