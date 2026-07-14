# API Error Codes

## Common error codes and what they mean

- **401 Unauthorized**: the API key is missing, invalid, or expired. Customers should
  regenerate their key from Settings > API Keys. Keys issued before 2025-01-01 on
  the legacy auth system were deprecated and must be regenerated.
- **403 Forbidden**: the API key is valid but the account's current plan does not
  include access to that endpoint. Basic plan accounts cannot call bulk-export
  endpoints; this requires a Pro or Enterprise plan.
- **429 Too Many Requests**: the account exceeded its rate limit. Basic plan is
  limited to 60 requests/minute, Pro to 600 requests/minute, Enterprise is
  configurable. The response includes a `Retry-After` header in seconds.
- **500 Internal Server Error**: a server-side failure. If this persists across
  multiple retries with exponential backoff, it should be escalated with the
  request ID from the `X-Request-Id` response header.
- **422 Unprocessable Entity**: the request payload failed validation. The response
  body contains a `field_errors` object listing exactly which fields failed and why.

## Webhook delivery failures

Webhooks are retried up to 5 times with exponential backoff (1m, 5m, 15m, 1h, 6h).
After 5 failed attempts the webhook is marked "dead" and must be manually
re-triggered from the Webhooks dashboard. Endpoints that fail to respond within
10 seconds are treated as failed deliveries.

## Escalation criteria

Escalate to a human agent if a customer reports correct credentials returning 401
errors intermittently — this pattern is associated with clock-skew or
infrastructure issues that self-service documentation cannot resolve.
