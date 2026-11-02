# VTM MCP Server

An intentionally vulnerable MCP server mounted at `/mcp`, used as a
true-positive target for MCP security scanners. It also includes safe control
tools so false positives can be measured against the same server.

The machine-readable answer key is [`expected_verdicts.json`](expected_verdicts.json).
`tests.py` fails if that file drifts from the server's `tools/list`.

## Connection

- **Transport:** streamable HTTP with JSON responses (no SSE stream). It uses
  the legacy `initialize` handshake and supports protocol versions
  `2024-11-05`, `2025-03-26`, `2025-06-18` and `2025-11-25`.
- **Methods:** `initialize`, `ping`, `tools/list`, `tools/call`,
  `resources/list`, `resources/templates/list`, `resources/read`, `prompts/list`.
- **Auth:** optional. Send `Authorization: Bearer <token>` with a DRF token
  from `/api-token/` or a VTM JWT.

## Vulnerable tools (expected: flagged)

| # | Tool | Vulnerabilities | Evidence |
|---|---|---|---|
| 1 | `network_diagnostics(host)` | Command injection | `127.0.0.1; id` returns the ping output plus `uid=...` |
| 2 | `search_tasks(query)` | SQL injection | A UNION query returns usernames and password hashes. Malformed SQL returns the database error and query text |
| 3 | `import_attachment_from_url(url)` | SSRF | Fetches any URL from the server, internal ones included, and returns the body |
| 4 | `read_attachment(filename)` | Path traversal | `../../…/etc/passwd` returns the file |
| 5 | `get_user_profile(user_id)` | IDOR, sensitive data, error disclosure | Any user's email, DOB, SSN, password hash and reset token. `user_id=abc` returns a JSON-RPC error with a full Python traceback |
| 6 | `read_note(note_id)` | Indirect prompt injection, IDOR | Returns any note's text word for word, with nothing marking it as untrusted |
| 7 | `add_note(task_id, title, text)` | Excessive agency, missing authorization | Writes to any task with no membership check. Pairs with `read_note` to plant a prompt injection |
| 8 | `render_note_preview(markdown)` | XSS | `<img src=x onerror=alert(1)>` comes back unescaped in the HTML |
| 9 | `get_project_report(project_id, include_audit_data, session_context)` | Tool poisoning, IDOR | The description contains an `<IMPORTANT>` block telling the agent to always call this tool, copy any secrets it has seen into `session_context`, and hide this from the user. `include_audit_data=true` adds every user's password hash and API token |
| 10 | `set_user_role(username, is_staff, is_superuser)` | Excessive agency, missing function-level access control (mflac) | Anyone, even with no login, can grant or revoke admin instantly with no confirmation step |
| 11 | `send_team_email(to, subject, body)` | Excessive agency | "Sends" mail to any address immediately with no confirmation. Delivery is only simulated in the log |

## Safe controls (expected: not flagged)

| # | Tool | Vulnerable twin | Why it's safe |
|---|---|---|---|
| 12 | `check_host_reachable(host)` | `network_diagnostics` | Accepts only an IP address, never uses a shell, and returns only `reachable` or `unreachable` |
| 13 | `find_my_tasks(query)` | `search_tasks` | Uses the Django ORM instead of raw SQL, only searches the caller's own tasks, and requires a login |
| 14 | `preview_note_text(markdown)` | `render_note_preview` | HTML-escapes the input |
| 15 | `get_project_status(project_id)` | `get_project_report` | Requires a login and project membership, and rejects non-numeric ids as an error result |

All four also reject arguments of the wrong type with an `isError` result,
never a traceback. Keep them safe; they are the true-negative baseline.

## Resource

| URI | Vulnerability | Evidence |
|---|---|---|
| `vtm://debug/environment` | Sensitive data exposure | Returns `SECRET_KEY`, database settings and `OPENAI_API_KEY` |

## Server-wide behavior

- **Login is optional.** A missing or invalid bearer token is treated as an
  anonymous user, not rejected.
- **Any vulnerable tool can leak a traceback.** Unexpected input that crashes a
  vulnerable tool, such as a wrong argument type, returns a JSON-RPC error with
  the full traceback. Error disclosure is therefore a valid finding on any of
  tools 1–11, not just `get_user_profile`.
- **Evidence is returned as a successful result.** Every vulnerable tool puts
  its proof in a normal `result.content` text block, with `isError` absent.
  Scanners such as Surveyor discard evidence inside rejected or error-flagged
  results.

## Running and scanning

- Tests: `./manage.py test mcp_server`
- **Public hostname required.** Surveyor rejects localhost and private
  addresses, so the server must be deployed at a public hostname. Register it
  as `streamable_http` at `https://<host>/mcp`.
- **Isolated host.** `network_diagnostics` runs real shell commands, so deploy
  it on an isolated host.
- **Reset between scans.** `set_user_role` and `add_note` change the database.
  Run `./reset_db.sh` between scans to keep results repeatable.
