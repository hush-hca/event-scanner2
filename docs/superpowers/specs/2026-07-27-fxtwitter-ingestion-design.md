# FxTwitter Ingestion Design

## Goal

Automatically ingest posts from configured official X accounts and support manual X status URL submission, using FxTwitter v2 as the data provider before passing normalized events to the existing scanner.

## Data Flow

Configured handles are polled from FxTwitter at a configurable interval. Manual status URLs are fetched on demand. Both routes normalize a post into `RawEvent`, preserve the canonical X URL, derive trust only from the configured handle allowlist, deduplicate by post ID/URL, and submit the event to the existing scoring pipeline.

## Configuration

- `X_WATCHED_HANDLES`: comma-separated official account handles.
- `FXTWITTER_POLL_INTERVAL_SECONDS`: integer seconds, default 60.
- `FXTWITTER_BASE_URL`: default `https://api.fxtwitter.com/2`.

## API

- `POST /v1/x/ingest-url`: takes a status URL and explicit token; fetches the post and returns its assessment.
- `POST /v1/x/poll`: checks every configured account once and returns processed, duplicate, and failed counts.

## Safeguards

- Only `x.com` and `twitter.com` status URLs are accepted.
- A manual URL is trusted only when its returned author handle is allowlisted.
- FxTwitter JSON `code` and HTTP status must both indicate success.
- A failed account must not stop polling of other accounts.
- The source URL remains unique in the audit store, preventing duplicate assessment and alerts.
- Token attribution remains explicit input/configuration; post text is not used to infer a tradable token.

## Verification

- Mock post and user-status endpoints.
- Test URL validation, allowlist trust, duplicate suppression, partial polling failure, and successful handoff to scoring.
