# Mobile inference status

Windows remains the only built and tested release target. The pack manager separates manifest, download, checksum, extraction, storage, and model-root discovery from the desktop UI, which is a useful starting point for mobile but is not proof of mobile compatibility.

The current inference path requires CTranslate2 4.8.3 and SentencePiece 0.2.2. The shipped dependency lock and native wheels target Windows. No Android or iOS runtime package, build recipe, device test, or memory/performance measurement is included. Android would need a supported arm64 CTranslate2 build (or a separately validated mobile runtime adapter), app-private storage and network permission; iOS additionally needs an iOS-compatible inference build and signing/toolchain validation. These remain implementation milestones, not supported features.

Before adding mobile claims, build from a clean environment for each target, install a pack, run both directions on-device in airplane mode, verify checksums and cancellation, and measure peak RAM, storage, latency, and battery impact. Do not share the Windows runtime version constraint as a mobile compatibility claim.
