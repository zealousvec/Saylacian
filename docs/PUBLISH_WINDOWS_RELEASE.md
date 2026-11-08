# Windows release publication checklist

**Status: not approved for publication.** This checklist is for maintainers. It does not mean an official binary exists.

## Before publishing

- [ ] Verify third-party redistribution rights for bundled native DLLs, fonts and other assets. See [the detailed release audit](GITHUB_RELEASE_CHECKLIST.md).
- [ ] Build the portable ZIP from the exact release commit using the existing Windows workflow; verify its SHA-256 and manifest.
- [ ] Test the extracted ZIP on a **separate, clean 64-bit Windows PC** without Python or Git: launch, script conversion, copy/paste, offline pack installation, translation and reopening.
- [ ] Confirm Windows security behavior without bypassing protections. If the unsigned binary is blocked, resolve signing/distribution rather than asking users to disable protection.
- [ ] Review documentation, privacy claims, licences and known limitations.

## Publish once approved

1. Sign in as a repository maintainer and open [Releases](https://github.com/zealousvec/Saylacian/releases).
2. Select **Draft a new release**; create an appropriate new version tag from the verified commit.
3. Title it **Saylacian v0.1.0a1 — Windows alpha** (or the version actually being released).
4. Attach the **verified** `Saylacian-Portable.zip` and its `.sha256` checksum. **Do not attach** the outer Actions artifact wrapper as the user-facing download.
5. Use the template below; mark it **pre-release**. Double-check the asset and source commit, then publish.
6. Check that an unsigned-out visitor can download the asset. Update [Get started](GET_STARTED.md) and the [main README](../README.md) to say the public download is available only after this succeeds.

## Release notes template

### Saylacian — Windows alpha

**Download:** Select `Saylacian-Portable.zip` under **Assets**, extract it, open the Saylacian folder and run `Saylacian.exe`. Keep the entire folder together. Python and Git are not required.

**First use:** For meaning translation, open **Offline language packs** (Ctrl+P) and download the relevant pack. The standard packs run offline after installation.

**Limitations:** Somali translation is experimental. Borama/Kaddare mappings and Old Nubian reading support are partial. No official Android/iPhone app or hosted website is included. Read [supported features](SUPPORT_MATRIX.md).

**Security:** Do not disable Windows security features to run an executable. Report blocked launches or errors through [Issues](https://github.com/zealousvec/Saylacian/issues).

**Licence:** Saylacian-authored code is AGPL-3.0-or-later; bundled third-party components retain their own terms.
