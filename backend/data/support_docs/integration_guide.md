# Integration Guide

## Connecting a new integration

1. Go to Settings > Integrations and select the provider.
2. Authorize access via OAuth. The account performing authorization must have
   admin permissions on both sides.
3. Choose which data streams to sync (contacts, events, or both).
4. Initial sync can take up to 2 hours for accounts with more than 50,000 records.

## Sync failures

- **"Authorization expired"**: the OAuth token was revoked on the provider's side,
  often because a password was changed there. Re-authorize from the Integrations
  page.
- **Partial sync / missing records**: usually caused by field mapping mismatches.
  Check Settings > Integrations > [Provider] > Field Mapping and confirm required
  fields are mapped.
- **Duplicate records after sync**: happens when a matching key (usually email) is
  not marked as unique on the provider's side. Enable "deduplicate by email" in
  the sync settings.

## Rate limits during sync

Large syncs respect the provider's own rate limits automatically and will pause
and resume rather than fail outright. A paused sync shows status "throttled" and
resumes automatically within the hour.

## Escalation criteria

Escalate to a human agent if a customer needs a custom field mapping that is not
supported by the standard mapping UI, since this requires engineering
involvement to configure.
