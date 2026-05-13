# AGENTS.md

## Project Overview

VTM is the Vulnerable Task Manager, an intentionally vulnerable Django application used for security training. It models a small task/project management system with users, groups, projects, tasks, notes, file uploads, password reset, a REST API, and an AI assistant.

The application is not intended to be production hardened. Many insecure patterns are deliberate training targets. When making changes, preserve intentional vulnerabilities unless the user explicitly asks to remove or mitigate them.

Primary application areas:

- `taskManager/`: Django project configuration plus the main task management app.
- `chatbot/`: AI assistant integration for querying task/project data.
- `taskManager/templates/taskManager/`: HTML templates for the task manager UI.
- `taskManager/static/taskManager/`: bundled frontend assets.
- `taskManager/fixtures/`: seed users, groups, projects, tasks, notes, and permissions.
- `vtmdb.sqlite3`: local SQLite database used by the training app.

Common local setup:

```sh
python3 -m venv vtm_venv
source vtm_venv/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py loaddata taskManager/fixtures/*
./manage.py runserver
```

Default training login from `README.md`: username `chris`, password `test123`.

## Agent Guidance

- Treat this as a vulnerable training application. Do not "clean up" security issues as incidental refactors.
- If a task touches a vulnerable code path, document whether the vulnerability is being preserved, expanded, or intentionally fixed.
- Prefer small, scoped changes that match the existing Django style.
- Do not replace intentional raw SQL, command execution, weak settings, CSRF exemptions, or auth flaws unless explicitly requested.
- Avoid destructive database or fixture changes unless the user asks for them.
- `vtmdb.sqlite3`, `mysite.log`, media uploads, and generated static output may contain local training state; avoid unnecessary churn.
- The OpenAI/chatbot integration depends on `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_BASE_URL` settings.

## Change Guidance

Work on VTM can improve maintainability, layout, static assets, components, tests, and developer ergonomics, but it must not silently remove or mitigate intentionally vulnerable training behavior. Treat the vulnerability chart in this file as the preservation checklist before changing routes, views, templates, forms, middleware, serializers, JavaScript, static behavior, fixtures, or settings.

- Keep the app Django server-rendered unless a task explicitly changes the architecture.
- Preserve route names, form actions, request methods, context variables, cookie behavior, and template rendering semantics unless the task explicitly asks to change them.
- During UI/static/template work, update markup and assets without incidentally adding CSRF protections, authorization checks, input sanitization, safer redirects, safer cookie flags, safer SQL, safer command execution, or stricter upload validation.
- Do not remove `|safe`, escaping behavior, hidden fields, user-controlled redirects, legacy endpoints, insecure debug/settings surfaces, or broad API/chatbot data access as cleanup.
- If a vulnerable behavior must be touched for UI compatibility, keep an equivalent training surface and call it out in the change summary.
- Add or update preservation tests when work could obscure, rename, or reroute a protected behavior.
- Remove legacy static assets only after confirming templates and JavaScript no longer reference them and the vulnerable training behavior below still exists.

## Known Intentional Vulnerabilities

This chart summarizes observed vulnerable behavior in the current codebase. It is a working inventory, not a guarantee that every training case is listed.

| Area | Files / Routes | Vulnerability | Training Purpose / Notes |
| --- | --- | --- | --- |
| Django configuration | `taskManager/settings.py` | Hardcoded `SECRET_KEY`, `DEBUG = True`, `ALLOWED_HOSTS = ['*']` | Demonstrates insecure deployment configuration and debug exposure. |
| Password storage | `taskManager/settings.py` | Uses `MD5PasswordHasher` | Demonstrates weak password hashing. |
| JWT/session cookies | `taskManager/views.py`, `taskManager/middleware.py`, `taskManager/settings.py` | JWTs are long-lived, signed with weak secret, set in non-HttpOnly and non-secure cookies; refresh rotation and blacklist disabled | Demonstrates token theft, replay, and weak token lifecycle controls. |
| CSRF protection | `taskManager/settings.py`, `taskManager/views.py` | CSRF middleware is disabled and several views use `@csrf_exempt` | Demonstrates CSRF exposure on profile, password reset, password change, and ping flows. |
| Login logging | `taskManager/views.py` | Failed and invalid login paths log usernames and plaintext passwords | Demonstrates sensitive data exposure through logs. |
| Open redirect | `taskManager/views.py` | Login and logout redirect to user-controlled `next` / `redirect` parameters | Demonstrates unvalidated redirect handling. |
| SQL injection | `taskManager/views.py` `/taskManager/search/` | Search builds raw SQL using unsanitized query text | Demonstrates classic SQL injection in search. |
| SQL injection | `taskManager/views.py` `/taskManager/forgot_password/` | Password reset lookup uses raw SQL with the submitted email | Demonstrates SQL injection in account recovery. |
| SQL injection | `taskManager/views.py` project details route | `Project.objects.extra()` interpolates `project_id` into a SQL fragment | Demonstrates unsafe query construction around path parameters. |
| Command injection | `taskManager/views.py` `/taskManager/ping/` | Builds a shell command from user input and executes it with `subprocess.getoutput()` using a blacklist filter | Demonstrates blacklist bypass and shell command injection. |
| Command injection / unsafe file handling | `taskManager/misc.py` | File upload helpers pass paths to `os.system("mv ...")` | Demonstrates shell-sensitive file handling and unsafe filename/path handling. |
| SSRF / URL fetch | `taskManager/views.py` upload flow | Server fetches arbitrary user-supplied URLs with `requests.get()` | Demonstrates server-side request forgery and unsafe remote file import. |
| File upload weaknesses | `taskManager/views.py`, `taskManager/misc.py` | Upload validation relies on extension/content-type assumptions and stores attacker-controlled names under web-served media | Demonstrates unsafe upload and content handling. |
| Authorization bypass / IDOR | `taskManager/views.py` profile routes | `profile_by_id` lets authenticated users edit arbitrary user profiles/groups/passwords by numeric ID | Demonstrates insecure direct object reference and privilege manipulation. |
| Authorization gaps | `taskManager/views.py` task/project/note routes | Some routes fetch objects before authorization checks or rely on partial project membership checks | Demonstrates access-control mistakes and object enumeration patterns. |
| Sensitive data exposure | `taskManager/views.py`, `taskManager/models.py` | User profiles include DOB and SSN; debug settings page renders `request.META` | Demonstrates exposure of personal and environment data. |
| API data exposure | `taskManager/serializers.py`, `taskManager/urls.py` | DRF endpoints expose users, profiles, files, notes, tasks, projects; some viewsets are broader than normal least-privilege designs | Demonstrates API reconnaissance and authorization review. |
| Stored/reflected XSS candidates | templates plus note/task/profile inputs | User-controlled text, image URLs, filenames, and profile fields flow into templates and redirects | Verify per-template escaping before changing; these are training surfaces. |
| DOM XSS | `taskManager/templates/taskManager/dashboard.html`, `taskManager/templates/taskManager/login.html` | Fragment-derived or decoded values are written into the document with unsafe DOM APIs | Demonstrates client-side injection and unsafe DOM writes. |
| Unsafe image redirect | `taskManager/views.py` `/taskManager/downloadprofilepic/` | Redirects to a stored profile image path without validation | Demonstrates untrusted URL/path use. |
| AI data access | `chatbot/tools.py`, `chatbot/views.py` | Chatbot tools include `get_users` and broad `search_database`, exposing users, profiles, notes, files, chat records, DOB, SSN, reset tokens, and other model text fields | Demonstrates tool authorization and data-minimization review. |
| AI write access | `chatbot/tools.py`, `chatbot/views.py` | Chatbot tools can add and update projects, tasks, and notes for accessible records | Demonstrates risks around autonomous tool use and state-changing assistant actions. |

## Preservation Tests

Focused regression tests live in `taskManager/test_preservation.py` and `chatbot/tests.py`. Run them when changing auth, search, upload, profile, chatbot, template, or tool behavior:

```sh
source venv/bin/activate
./manage.py test chatbot taskManager.test_preservation
```

## Useful Commands

```sh
./manage.py runserver
./manage.py test
./manage.py migrate
./manage.py loaddata taskManager/fixtures/*
./reset_db.sh
```
