# mail-janitor — Project Brief

## Goal
Build a local-first inbox cleanup workbench that can:
- connect to multiple mail accounts
- scan inbox folders
- group emails by sender/domain
- detect standard unsubscribe headers
- support dry-run bulk actions
- allow bulk archive/delete
- support unsubscribe actions only where standards-based unsubscribe exists

## Runtime constraints
- Must run locally in Docker
- Must be compatible with Once
- Must serve on port 80
- Must expose `/up` returning HTTP 200
- Must persist writable state under `/storage`

## Scope for MVP
- Local only
- No public auth
- No billing
- No hosted SaaS
- No n8n dependency
- No OAuth in v1
- Support provider types:
  - gmail
  - outlook
  - generic_imap

## Safety rules
- Dry-run must be default
- No destructive action without explicit review
- Never touch Sent, Drafts, or Spam by default
- Log every action
- Support protected senders/domains
- Support max affected message threshold

## Tech stack
- Python 3.12
- FastAPI
- Jinja2 templates
- SQLite
- imap_tools
- Docker

## Current state
- Repo initialized
- Docker base app runs
- `/up` works
- Base Once-compatible structure exists

## Immediate objective
Have the agent audit the current repository and propose the minimum set of changes needed to implement:
1. account configuration
2. IMAP connection testing
3. inbox scan
4. sender/domain aggregation UI
without destructive actions yet
