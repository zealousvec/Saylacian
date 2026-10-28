# Optional online translation

Saylacian defaults to local translation. Installed offline packs remain the primary route and do not depend on any hosted quota. Online translation is optional and requires explicit provider configuration; it is not silently enabled when a pack is missing.

The app can use a user-operated Saylacian service or Cloudflare Workers AI. Online requests send the entered text to the selected provider. Review that provider's privacy terms, capacity, costs and quotas before use. Saylacian does not promise unlimited online capacity or host a public translation service.

Configuration uses environment variables: `SAYLACIAN_TRANSLATION_PROVIDER` (`offline`, `auto`, `selfhosted` or `cloudflare`); a self-hosted endpoint uses `SAYLACIAN_TRANSLATION_URL` and optionally `SAYLACIAN_SERVICE_TOKEN`; Cloudflare uses `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`. Never put tokens in source code or share them in public issues. Do not send sensitive text to a provider you do not trust.

For multi-line input, Saylacian submits each nonblank line as a separate request to preserve line boundaries. This increases request count and can reduce context between lines. Blank lines and line endings stay in the displayed result.
