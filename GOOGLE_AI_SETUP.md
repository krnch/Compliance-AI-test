# Google AI key setup — save now, configure privately later

Verified against project source and Google's documentation on September 24, 2026. No credentials were inspected, no model calls were made, and no backend or billing settings were changed to write this guide.

## Is a free Google AI key all that is needed?

**No. One valid Gemini API key can authenticate both answer generation and document embeddings, subject to model access and quota. It is only one prerequisite.** You do not need a separate key per model or regulation.

The [published frontend](https://gentle-field-09e568710.4.azurestaticapps.net/) is live. Its existing external backend is https://compliance-policy-ai-619596825255.us-central1.run.app and returned HTTP 500/503 during deployment assessment. Its actual credentials, deployed index and failure cause have not been verified. A new key alone cannot be promised to fix it.

| Requirement | What this project needs |
|---|---|
| Credential | Backend environment variable `GOOGLE_API_KEY`, with `AI_PROVIDER=gemini`. |
| Model access | Working generation **and** embedding models with available Free-tier quota. |
| Regulation index | Populated ChromaDB collections at the backend's `storage/chroma_db` path; a fresh clone does not contain this gitignored database. |
| Running backend | Healthy Python application, dependencies and deployment. Free Gemini API access does not provide hosting. |
| Browser access | Backend CORS permits the current frontend origin; check the deployed setting rather than assuming it matches source defaults. |
| Public-use safety | Sanitize rendered AI Markdown/HTML and review backend abuse controls before real public AI use. CORS alone is not authentication or quota protection. |

## 1. Get a key from your Google account

1. Open **[Google AI Studio API keys](https://aistudio.google.com/api-keys)** and sign in with the Google account you want to use. Check the account avatar so you do not accidentally use a work account.
2. Accept the terms if prompted. A new AI Studio user may receive a default project/key. Existing Google Cloud users may need **Dashboard → Projects → Import projects** to make an authorized project visible.
3. Open **[Projects](https://aistudio.google.com/projects)** and check the project's **Billing Tier**. For this free-only setup, use a project confirmed as **Free**. If needed, create a separate personal project through AI Studio's project creation flow, subject to account/organization permissions, then verify its tier.
4. Return to **API keys → Create API key**, select that project and give the key a recognizable name, such as `compliance-ai-backend`. An existing valid key in that Free project can also be used.
5. Copy the key privately into your password manager or intended backend secret store. **Do not paste it into chat, an issue, a PR, a screenshot, the frontend or a Git-tracked file.** Record the project ID and key name separately; those are enough to locate it later.
6. Check **[Rate limits](https://aistudio.google.com/rate-limit)** for that project and the models you intend to use. Having a key does not guarantee usable quota for every model.

**Stop at any payment prompt.** Do not select Set up billing, link a billing account, buy credits or enable auto-reload for this free-only task. A key created inside an already-paid project inherits that billing status; a new key does not make that project free. Do not disable billing on the existing Cloud Run project, since that could interrupt other services. A separate verified-Free API project can be used without changing the hosting project's billing.

A Gemini consumer app/Google AI subscription is not a substitute for creating a Gemini **API** credential and checking its project tier. Multiple keys in the same project share project quotas; they do not multiply the free allowance. Availability depends on supported region/account eligibility as well as model and tier.

### Existing keys and permissions

Google's current [key documentation](https://ai.google.dev/gemini-api/docs/api-key) says new AI Studio keys have been **authorization keys** since May 28, 2026, with standard-key rejection scheduled for September 2026. Check **Key Type**: for an old Standard key, create a replacement auth key, configure and verify it, then revoke the old one. Do not judge validity from a key prefix or assume an old tutorial's key format still applies.

If Create API key is unavailable, ask the project administrator for the necessary permissions, or use a personal project you are authorized to manage. Do not bypass organization restrictions. New auth keys are Gemini/Generative Language API restricted by default. Do not add browser-referrer restrictions to this server-side key. IP restrictions require verified stable backend egress; the Cloud Run hostname is not an outbound IP address.

## 2. Where to update it later

### Local backend only

Use the existing [local setup instructions](README.md#local-setup) and [backend environment example](backend/.env.example). From the backend directory, copy the example to a local file named `.env` **only if that file does not already exist**. Otherwise edit the existing local file without overwriting other settings. Enter the key privately in the editor:

- `GOOGLE_API_KEY`: your real key, stored locally only.
- `AI_PROVIDER`: `gemini`.
- `ALLOWED_ORIGINS`: the frontend origin used for that test.

The local dotenv file is gitignored and excluded from the container build context. Never force-add it to Git or remove those exclusions. Restart the backend after updating it. Existing process environment values can override dotenv values, so an old exported `GOOGLE_API_KEY` must also be updated or removed privately if present. Avoid secret values in terminal commands/history.

**Use `GOOGLE_API_KEY` for this repository.** Although Google SDK documentation also describes `GEMINI_API_KEY`, [the backend](backend/main.py) and [ingestion script](backend/scripts/ingest.py) explicitly read `GOOGLE_API_KEY`. Updating only a local file does **not** update the live Cloud Run service.

### Existing deployed Cloud Run backend — later, after ownership/cost review

Do not create a replacement service or enable paid services just to enter the key. First identify the Google Cloud project and existing service you are authorized to manage; the public URL alone does not establish ownership. Cloud Run, builds, image storage and Secret Manager have separate pricing/allowances that have not been verified here.

For production, Google's recommended approach is **Secret Manager → Cloud Run environment variable reference**:

1. In the correct Google Cloud project, open **Secret Manager**. Use an existing app-specific secret or, after approving any separate costs/setup, create one such as `compliance-google-api-key`. Paste the key privately as its secret value. For rotation, add a new version to the existing app secret; do not change a shared secret blindly.
2. Give the Cloud Run **runtime service account** Secret Manager Secret Accessor on that specific secret. This runtime account is not necessarily the service account bound to the Gemini auth key. The person editing the service also needs appropriate Cloud Run/IAM permissions.
3. Open **[Cloud Run services](https://console.cloud.google.com/run/services)**, select the existing backend and open **Containers → Variables and Secrets → Reference a secret**. Some console layouts start with **Edit & deploy new revision**.
4. Set the environment variable name to **`GOOGLE_API_KEY`**, choose the app secret and pin a specific secret version. If an ordinary variable already has that name, replace its binding rather than adding a duplicate. Merely creating a secret, or mounting a file without code changes, will not populate this variable.
5. Keep **`AI_PROVIDER=gemini`**. Review `ALLOWED_ORIGINS`: it must include **`https://gentle-field-09e568710.4.azurestaticapps.net`**. Preserve other intentionally supported origins. Source parses comma-separated origins without trimming, so use no spaces or trailing slash. The default `*` permits origins broadly; it is not evidence of the actual live setting.
6. Review the diff, then **View diff & redeploy → Deploy changes** (or the equivalent new-revision action). Ensure the ready revision receives the intended traffic. Environment secrets are read at instance startup; adding a secret version alone does not update an already-running revision pinned to an older version.
7. Follow the verification checklist below before declaring recovery. For routine rotation, revoke the old key after the new revision works. If a key is exposed, revoke it promptly and review usage; temporary downtime is preferable to continuing abuse.

**Not the right places for this key:** frontend JavaScript/HTML, Azure Static Web App settings, or the GitHub secret `AZURE_STATIC_WEB_APPS_API_TOKEN_PERSONALWEBSITES`. That GitHub secret is an **Azure deployment token**, not a Gemini credential. Changing it will not configure Google Cloud Run.

## 3. Model and document-index requirements

Current source uses:

- Generation: `gemini-2.5-pro` → `gemini-2.5-flash` → `gemini-2.5-flash-lite` in [the model chain](backend/usage_tracker.py). The initial preference is Pro, even though Flash is labelled primary.
- Embeddings: `gemini-embedding-001`, hardcoded in both [ingestion](backend/scripts/ingest.py) and [query handling](backend/main.py).

These are **source configuration facts, not a promise that those models are currently available/free for your project**. Verify current [pricing](https://ai.google.dev/gemini-api/docs/pricing), [deprecations](https://ai.google.dev/gemini-api/docs/deprecations) and project quota. The dashboard's hardcoded limits are not Google's authoritative limits. Model changes require reviewed code changes; there is no documented model-name environment override here. Changing the embedding model requires compatible re-ingestion, not simply reusing old vectors.

After configuring the private key and installing the backend dependencies, initialize one regulation first. From the backend directory, the command is `python scripts/ingest.py --regulation hipaa`. This makes real embedding requests and consumes quota. **It deletes/recreates the selected collection**, so back up any existing index before re-running it. Running `python scripts/ingest.py` with no regulation argument processes all five source documents; there is no `--regulation all` option.

All five source text files are tracked under [backend/data](backend/data). Generated vectors are not in Git. A local index is not automatically transferred to Cloud Run. The existing container build can include a prepared index if it exists in the build context, but there is no automatic ingestion step in [the Dockerfile](backend/Dockerfile). Backend recovery must deliberately supply the correct populated index and plan persistence; runtime filesystem writes must not be assumed durable across Cloud Run instance replacement. This guide does not run Docker or deploy anything.

## 4. How to confirm it really works

Later, after backend repair/configuration:

- [ ] The backend `/health` returns 200. This is only a server check: it does not call Gemini or inspect the index. Its free-tier notice is static text, not a billing check.
- [ ] `/debug-config` reports `ai_provider: gemini` and key presence. Presence is **not** key validity; do not add secret values to this response or logs.
- [ ] Required ChromaDB collections are populated. `/regulations` only returns configured names and does **not** prove ingestion succeeded.
- [ ] Both the configured embedding and generation models succeed within the project's Free allowance.
- [ ] A public, non-sensitive sample such as “What is Protected Health Information?” gets a real, cited answer for HIPAA through `/ask`.
- [ ] The same request works from the published frontend, with no CORS error. If the backend URL changes, review all three callers: [frontend/app.js](frontend/app.js), [frontend/dashboard.html](frontend/dashboard.html) and [frontend/models.html](frontend/models.html).
- [ ] Review [AI Studio usage](https://aistudio.google.com/usage), live limits, privacy terms and backend hosting costs independently.

| Symptom | Check next |
|---|---|
| Invalid key / 400 | Correct private value, current auth-key type and the active revision's variable/secret binding. |
| 403 / permission denied | Account/project eligibility, enabled API, key restrictions and required permissions; do not broaden permissions indiscriminately. |
| Model not found / 404 | Current model availability and API support. A new key cannot revive a retired model. |
| 429 / resource exhausted | Actual project/model quota; wait/back off or reduce usage. Do not auto-upgrade to paid or create keys to bypass limits. |
| 503 “Vector DB not found” | Supply the populated index at the backend's expected path. |
| Missing collection / empty retrieval | Ingest the selected regulation and verify compatible embeddings. |
| Backend 500/503 generally | Inspect sanitized runtime/startup logs; do not assume all failures are credential-related. |
| Browser CORS failure | Exact deployed frontend origin, response headers and backend health. |

Unit tests use dummy credentials and mock both Google client constructors and query responses, including model fallback. [The pytest configuration](backend/pytest.ini) blocks Internet sockets so accidental API calls fail locally rather than reaching Google. **Do not put your real key in unit-test CI.** Earlier failures were caused by unmocked model-metadata calls; those failures did not diagnose the live backend. Passing unit tests likewise do not prove live credentials or backend health.

## Free-tier privacy and official references

Free does not mean unlimited, a production SLA, or that every model is included. Free and paid data-use terms differ; use only public/non-sensitive regulatory examples during free testing. Do not send patient records, personal information, confidential company policies or real customer data without an appropriate privacy review. Budgets/alerts are not hard cost caps.

- [Create/manage Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key)
- [Billing and project tiers](https://ai.google.dev/gemini-api/docs/billing)
- [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Pricing and data-use comparison](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API terms](https://ai.google.dev/gemini-api/terms)
- [Supported regions](https://ai.google.dev/gemini-api/docs/available-regions)
- [Cloud Run secret configuration](https://docs.cloud.google.com/run/docs/configuring/services/secrets)

You can create and store the key now, then configure it privately later. No key needs to be sent to the assistant.