# mail-janitor

Local-first inbox cleanup workbench for bulk sender analysis, unsubscribe detection, and safe archive/delete workflows.

## Goals

- Scan inboxes across multiple providers
- Group emails by sender/domain
- Detect unsubscribe-capable senders
- Dry-run bulk cleanup actions
- Support safe archive/delete workflows

## Local development

```bash
docker compose up --build

Open:
http://127.0.0.1:8088

Healthcheck:
http://127.0.0.1:8088/up
