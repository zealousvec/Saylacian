# OpenLID Somali language detection

Saylacian's optional Somali detector downloads the int8 ONNX conversion at the pinned revision in [`somali_detection_manifest.json`](../saylacian/core/data/somali_detection_manifest.json). The upstream model card identifies the base model as `alexneakameni/language_detection`, lists MIT for that model, and names `hac541309/open-lid-dataset` as its training data. The dataset card lists GPL-3.0. Those upstream declarations are recorded separately here; this notice does not determine whether every underlying training-data right permits every use.

The ONNX conversion is provided by the ONNX Community model repository and is not bundled with Saylacian. Saylacian downloads the selected files directly from the pinned Hugging Face revision and verifies their byte counts and SHA-256 hashes before activation. Review the upstream model and dataset terms for your intended use.

Sources:

- [ONNX model card](https://huggingface.co/onnx-community/language_detection-ONNX)
- [Base model card](https://huggingface.co/alexneakameni/language_detection)
- [Training dataset card](https://huggingface.co/datasets/hac541309/open-lid-dataset)
- [Pinned ONNX model revision](https://huggingface.co/onnx-community/language_detection-ONNX/tree/859bc93be10a6f8ad4a070911a4caaa092cdcd2e)
