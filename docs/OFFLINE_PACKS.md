# Offline translation packs

Pack downloads are optional and begin only after you choose **Download** in Saylacian. Each pack is downloaded over HTTPS, checked against its pinned file sizes and SHA-256 hashes, staged, then activated. Progress and cancellation are available in the app. No model weights are included in this source checkout.

| Pack | Languages | Download size | Model licence |
|---|---|---:|---|
| French / English | English ↔ French | about 166 MiB | MIT |
| Somali / English | English ↔ Somali Latin | about 300 MiB | Apache-2.0 |
| Optional Somali translation model | English → Somali | about 62 MiB | CC BY 4.0 |
| AfriSLM Somali / English | English ↔ Somali Latin | about 672 MiB | Apache-2.0 model; see training-data terms |
| Optional Somali detection model | Somali input detection | about 25 MiB | MIT model; GPL-3.0 training dataset |

Installed packs are stored in the user's application-data folder, outside the project checkout. Use **Offline language packs** to see installed packs, install updates, cancel downloads or remove a pack to reclaim storage. Updating creates a versioned install; old versions remain until removed, so an update can temporarily need extra disk space.

The Somali detection pack is optional. After download, it can recover Somali input that the existing detector leaves uncertain. It does not translate text, and the existing English/French results take precedence. Detection runs on device; its model and runtime dependencies are pinned and work offline after installation.

The optional English-to-Somali pack uses a separate CTranslate2 model. Install the standard Somali/English pack first: Saylacian will not install the add-on without it, and will not remove the standard pack while the add-on is installed. The app tries the add-on first for English-to-Somali and falls back to the standard pack when its output appears copied, unreadable, repetitive or unfinished. This model has no published score in its model card and still needs fluent-speaker review.

AfriSLM is a separate, larger local model for both English↔Somali directions. Install the CPU runtime in the same Python environment as Saylacian with `python -m pip install -r requirements-afrislm.txt`. It uses `llama-cpp-python` and runs on CPU; first use can take longer while the model loads. If the runtime is missing or rejects a result, Saylacian uses another installed Somali model. AfriSLM is listed as Apache-2.0, but its model card also describes CC BY-NC-4.0 synthetic training data and an NLLB-200 teacher model under CC BY-NC-4.0. These are distinct upstream terms and need review before commercial redistribution. [AfriSLM model card](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B) · [llama-cpp-python CPU install](https://github.com/abetlen/llama-cpp-python).

On devices with four or fewer logical processors, Saylacian limits translation and optional language-detection inference to one CPU thread, uses a smaller beam for the standard translation route, and skips AfriSLM automatically in favour of the smaller Somali model. On devices with more logical processors, AfriSLM can still be slow because it is a large model.

In Saylacian's first 120-pair FLORES-200 sample, the optional route with fallback scored BLEU 10.755 / chrF++ 40.069; the standard pack scored 5.353 / 29.882. A second sample exposed 11 candidate results that ended with an unprompted ellipsis, so the app now falls back for those likely incomplete translations. With that guard, the second sample scored 10.470 / 37.983 versus 4.432 / 29.789 for the standard pack, with 31 fallbacks among 120 inputs. These are small automatic comparisons, not proof of fluent or meaning-preserving Somali. See the [full method and limitations](TRANSLATION_QUALITY.md#optional-english-to-somali-model-on-flores-200).

The optional detector is a fallback for uncertain short text; confident English or French results still take precedence. Its Somali threshold is 0.98. In a deterministic sample of 67 short, verified Somali texts from Qor, the integrated detector identified 38, compared with 33 from the existing route. In 11,386 short MASSIVE test texts from 52 non-Somali locales, it made no Somali predictions at that threshold. At 0.90, it identified 45 Qor texts but also made one Somali prediction in the MASSIVE sample. The higher threshold reduces that observed risk but misses some Somali inputs. Dataset labels are proxies, not specialist-verified language judgments; these samples do not establish general accuracy.

Translation packs work locally without a network connection, account, per-request fee or artificial daily quota. Somali output has not had fluent-speaker review, so check important translations before relying on them. See the [support matrix](SUPPORT_MATRIX.md).

The exact upstream repositories, revisions, hashes, sizes and licences are in `saylacian/core/data/model_manifest.json`, `saylacian/core/data/somali_model_manifest.json`, `saylacian/core/data/somali_synthetic_manifest.json` and `saylacian/core/data/somali_detection_manifest.json`. Model terms are separate from the Saylacian code licence; see [third-party notices](../THIRD_PARTY_NOTICES.md).
