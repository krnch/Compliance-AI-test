# Frontend-only Free deployment

The owner approved publishing the existing frontend first and repairing its external AI backend later. **Serving these pages is not proof that AI chat, model status or the usage dashboard works.** The Google Cloud Run API remains unchanged and returned 500/503 during assessment. No simulated responses are added.

For the deferred backend setup, see [Google AI key setup](GOOGLE_AI_SETUP.md). It explains how to obtain a key in a verified-Free project, update the backend privately later, and check model access, vector data and CORS. No credential or cloud configuration is changed by that guide.

## Published artifact

`node scripts/prepare-public-site.mjs` copies exactly six public files from `frontend/` plus the separate public configuration into `.public-site/`. It rejects symlinks and pre-existing output. No backend code, vector data, environment files, repository metadata or credentials are published. The source frontend configuration remains in Git but is replaced by the public deployment configuration in the artifact; no SPA fallback is needed for these four HTML pages.

## Azure target

- Subscription: personalwebsites (`0d47c761-157e-485c-bfd6-e320a9ed6a7e`).
- Existing resource group: `rg-personalwebsites-prod-c561`.
- App: `swa-compliance-prod-e529`, Central US, **Free**.
- No paid supporting services, managed API, enterprise CDN, new custom domain, or Mac Docker.
- Frontend: **https://gentle-field-09e568710.4.azurestaticapps.net/**. Provisioned and directly uploaded on September 24, 2026. All 22 HTTPS/content/security-route checks passed at 02:41:27 UTC; this does not establish backend health.

## GitHub updates

The workflow validates PRs without deployment secrets; only main pushes/manual main runs deploy. Actions are commit-pinned with read-only repository permissions and no persisted checkout credentials. A dedicated token for this app was configured privately under `AZURE_STATIC_WEB_APPS_API_TOKEN_PERSONALWEBSITES` at 02:41:42 UTC on September 24, 2026; no token is committed or printed.

No automatic PR merge. The initial authorized direct artifact upload is separate from GitHub automation, which still requires owner review/merge and a successful main deployment run. Until then, main and the live configuration differ; later main deployments can overwrite unmerged changes. The existing Python test workflow remains unchanged and may report independent backend dependency/test issues.

## Acceptance boundaries

Verify every public file, valid TLS, blocked admin/API/backend/config source routes and the four portfolio redirects after deployment. `/.auth/me` is an Azure-managed endpoint and may return an anonymous null principal. AI restoration requires separate backend diagnostics, model configuration and initialized vector data. The Free frontend estimate is $0 within Free limits; external services have separate costs and quotas and are not deployed by this workflow.