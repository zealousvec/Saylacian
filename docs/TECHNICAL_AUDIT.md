# Saylacian technical audit

**Scope/date:** Local branch `codex/release-prep` at `0f771f1` plus one uncommitted local path-normalization fix. Remote `main` points to `0f771f1`. This is a source review, not a security certification or a linguistic endorsement. Public repository metadata was viewed on 2026-10-24; the `gh` CLI was unavailable, so repository settings and private Actions details could not be queried through an authenticated CLI.

## Executive assessment

The repository is a real Python/Kivy application with shared conversion/translation modules, explicit model manifests, and a useful Windows CI workflow. It is an experimental alpha. The English↔French offline smoke route is testable. Somali translation and historical chart mappings are not quality-validated. The largest release-quality gaps are linguistic evaluation and the inconsistency between source/UI/docs about Nubian routes. A small Windows path-alias issue caused public CI to fail; a one-line local fix is now covered by the formerly failing test, but CI has not rerun because the fix is not pushed.

## Checks observed

- Current local test suite after the fix: **80 passed, 66 subtests passed** (9.60 seconds). Model files exist in the ignored local `models/` tree, so local model smoke tests ran; these results are not what a clean CI clone will see.
- Focused regression test for model-pack roots: **1 passed** after normalizing the returned folder using `Path.resolve()`.
- `compileall`, the exact workflow Ruff correctness selection, Ruff formatting check, `pip check`, release safety scan, and `git diff --check` passed in the earlier local verification run.
- Broad default Ruff lint reported 35 findings outside the CI's deliberately narrow correctness selection. They include unused imports, style simplifications, broad exception catches and a few minor quality issues; no broad cleanup was attempted.
- GitHub Actions for `0f771f1` reported 67 passed, 12 skipped, and one failure in `tests/test_model_packs.py::ModelPackTests::test_download_verifies_hash_installs_version_and_reports_progress`. Failure compared Windows short-path alias `RUNNER~1` with long path `runneradmin` for the same folder. The same test now passes locally after the path fix. Workflow has not run on that fix.
- `gh` command-line tooling is not installed, so authenticated repository settings and up-to-the-minute run details could not be queried locally. The public repo page is accessible and still shows a potentially misleading “non-profit” description; AUTHORS.md says the project is not a registered nonprofit.
- No new clean clone was created in this audit pass. Earlier project records describe a fresh-clone test; do not treat that historical report as a new independent reproduction here.

## Findings

### Medium — public CI currently fails; local repair is uncommitted

**Evidence:** `ModelPackManager.active_model_roots()` returned a resolved install path inconsistently on Windows. Windows CI compared the returned string with another representation of the same path and failed. The local line in [model_packs.py](../saylacian/core/model_packs.py#L224) now appends `folder.resolve()`. The formerly failing regression test passes locally. The workflow is [ci.yml](../.github/workflows/ci.yml).

**Impact:** The latest known public workflow was red, so the public source snapshot does not have green CI evidence. Local fix is not in remote history.

**Next:** Review the one-line diff, commit/push only after owner approval, then confirm a new Windows Actions run passes. No publication was done in this audit.

### Medium — Nubian support descriptions conflict

**Evidence:** [transliteration.py](../saylacian/core/transliteration.py#L200) implements Old Nubian Coptic-script→scholarly Latin and reverse conversion (reverse is ambiguity-aware/experimental); [capabilities.py](../saylacian/core/capabilities.py#L23) declares those routes. `main.py` recognizes Coptic and presents an Old Nubian option. In contrast, [SUPPORT_MATRIX.md](SUPPORT_MATRIX.md) says “Nubian unsupported and underspecified,” the website template says Nubian conversions are unavailable, and the published README says Old Nubian has no verified general converter.

**Impact:** Users and contributors cannot tell that a narrow historical transliteration exists, while modern Nubian varieties are genuinely unsupported. Coptic script alone does not identify a language.

**Next:** Align README, support matrix, website copy, and capability descriptions. State precisely: an Old Nubian table-based transliteration exists; reverse is experimental; modern Nubian languages are unavailable. Require language/script expert review before upgrading status.

### Medium — repository description makes unsupported nonprofit claim

**Evidence:** Public GitHub About text says “non-profit language-preservation software.” [AUTHORS.md](../AUTHORS.md) states the project is independent and not a registered charity/nonprofit.

**Impact:** Public repository metadata overstates legal status and may mislead users or partners.

**Next:** Owner/repository admin should change the GitHub description to neutral wording such as “Open-source experimental language and script preservation app.” This is account/repository metadata and was not changed.

### Medium — Somali quality is not established by the tests

**Evidence:** [translation.py](../saylacian/core/translation.py#L139) labels Somali paths experimental and Somali↔French uses English pivot. The tests include fixed expected strings and guarded candidate examples, but no independent human-quality assessment. TICO test fixture and evaluation records exist; they are not proof of community-accepted Somali.

**Impact:** Passing software tests can be mistaken for translation accuracy. Model output may be fluent-looking but semantically or grammatically wrong.

**Next:** Build a versioned, consented evaluation corpus, use independent fluent reviewers, report metrics by domain/direction, track uncertainty, and publish examples of failures. Keep warnings visible until evidence supports a change.

### Medium — historical script mapping claims need consistent boundaries

**Evidence:** Osmanya has a Unicode mapping with ambiguous reverse distinctions. Borama/Kaddare are partial chart-derived mappings encoded in private-use area and separately licensed CC BY-SA. Old Nubian mapping is a scholarly table with reverse ambiguities. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [SCRIPT_FEASIBILITY.md](SCRIPT_FEASIBILITY.md) describe sources and terms.

**Impact:** Table transcription does not establish accepted spelling, word-level orthography, or community consensus. PUA glyphs can be misread outside Saylacian.

**Next:** Keep each route marked experimental; add independent transcription checks, native/community review where available, explicit uncertainty/alternatives, and test fonts/rendering separately from mapping accuracy.

### Low — CI does not exercise installed translation packs

**Evidence:** [ci.yml](../.github/workflows/ci.yml) installs Python requirements and runs tests without downloading models. `tests/test_translation.py` uses `skipUnless` when expected model files are absent.

**Impact:** CI proves route guards and packaging logic, but not inference with all downloadable weights. Downloading hundreds of MiB on every CI run would add cost/flakiness.

**Next:** Keep normal CI lightweight; add a separately triggered, checksum-verified integration workflow or documented scheduled/manual pack validation. Do not make model weights ordinary Git artifacts.

### Low — broad lint has deferred cleanup

**Evidence:** Broad Ruff scan reports 35 findings outside the enforced CI selection; CI checks syntax/runtime-risk categories E9/F63/F7/F82 only.

**Impact:** The code passes correctness lint but has some maintainability/style noise. Automatic mass-fixing risks obscuring behavior in the large UI module.

**Next:** Triage by file and apply small reviewed changes when touching the relevant area; consider gradually expanding CI rules.

## Security, privacy, and reliability review

- **Model downloads:** Manifest hashes and sizes are checked; relative paths are validated; install uses staging/versioning. This is a good integrity design. A hash proves downloaded bytes match the manifest, not that upstream content is benign or its licence is correctly declared.
- **Self-hosted API:** Compose requires a token; Caddy provides TLS; request body and text length, concurrent translations and worker threads are bounded; text is not included in application log messages. It is optional and not deployed as a public service. A single shared token must not ship in a public client.
- **Desktop diagnostics/history:** User data stays local in normal offline mode, but history and diagnostic files are sensitive local data. Keep paths private and avoid attaching logs publicly without review.
- **Website:** local Flask app has request limits/headers covered by tests, but no production hosting configuration or operational security review was found. Do not expose the development server directly to the internet.
- **Source release:** model weights and native Windows DLL bundles are outside the source tree. Third-party assets have separate license notices. Binary distribution requires its own dependency/DLL and font-notice audit.
- **Capacity:** offline local inference has no per-request vendor charge but is constrained by device CPU, RAM, storage and user download. Self-hosted capacity is bounded; it is not unlimited service capacity.

## Architecture and platform review

The core/UI separation is workable for a small app, and the same core can be called from a local website. `main.py` is large (roughly 900 lines) and mixes screen lifecycle, clipboard, worker coordination, and app-level actions; that is the main maintainability pressure. Extracting modules may help later, but should be done with behavioral tests and no UI redesign.

Windows is the most developed target. The latest package runtime could not be independently verified in this pass. Android/iOS viability is a roadmap item, not a present capability: no device builds are verified. Accessibility and usability require hands-on review beyond code tests.

## Licensing / attribution

The root `LICENSE` is the official AGPLv3 text; project metadata marks AGPL-3.0-or-later for code the licensor owns or can license. It does not relicense fonts, model weights, historical charts/mappings, datasets or Python dependencies. See [third-party notices](THIRD_PARTY_NOTICES.md), [chart notices](../notices/HISTORICAL_SCRIPT_CHARTS.md), and [asset licenses](THIRD_PARTY_NOTICES.md). Binary repackaging has additional transitive native-library obligations.

## Worktree state and actions not taken

Current branch: `codex/release-prep`, aligned to local `main` and `origin/main` at `0f771f1`. One uncommitted code change exists in `saylacian/core/model_packs.py` (Windows path normalization described above). The five new handover documents are local changes. No commit, push, release, repository-setting change, or UI modification was made.
