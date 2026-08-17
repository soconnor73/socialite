# Security Backlog

Started from a validation pass over `SECURITY_REVIEW.md`, then extended with two
follow-up rounds: an OWASP Top 10 (2021) pass, and a full Docker build
verification once local builds became possible again. Full write-ups for
resolved items live in their commit messages (referenced below); this file
now only carries what's still open.

## Open / deferred

### Container runs as root — deferred
`docker/Dockerfile` has no `USER` directive; nginx's master process and `cron`
run as root. nginx's *worker* processes — which parse and serve all untrusted
HTTP input, the actual attack surface — already run unprivileged via the base
`nginx:stable` image's default `user nginx;` config, so the residual risk is
limited to the master process and a `cron` job that only ever runs a fixed,
non-attacker-influenced command.

A full non-root migration needs: a non-root-friendly scheduler in place of
system `cron` (e.g. `supercronic`), nginx bound to a non-privileged port (with
a matching Traefik `loadbalancer.server.port` label update in
`docker-compose.yml`), and ownership/permission changes for `/app`,
`raw_html/`, `events/`, and nginx's runtime dirs. Deliberately left as-is per
2026-08-16 decision — `security_opt: no-new-privileges:true` is in place in
`docker-compose.yml` as a compensating control in the meantime.

### SRI on Google Fonts links — intentionally skipped, not a TODO
`index.html`'s Google Fonts `<link>` tags have no Subresource Integrity hash.
Google's font CSS responses vary by `User-Agent`, so a fixed SRI hash would
break font loading for a large fraction of visitors — this is a known
SRI/Google-Fonts incompatibility, not an oversight. Not expected to change.

## Resolved

All fixed and verified; see the referenced commit for full detail on each.

| # | Finding | Commit |
|---|---|---|
| 1 | `docker.sock` mounted into the app container (root-equivalent host access, unused) | `a47729d` |
| 2 | Stored XSS: scraped `show.title`/`show.venue` interpolated into `innerHTML` (list view + calendar grid) | `a47729d`, `184bf9b` |
| 3 | `javascript:` URI injection via unvalidated scraped ticket links | `a47729d` |
| 4 | Missing nginx security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) | `c8b17a9`, `2872de0` |
| 5 | Entire source tree + runtime scrape cache publicly served via `root /app` with no path restriction | `52c1a38` |
| 6 | SSRF: `mn_united_fc.py`/`minneapolis.py` built outbound fetch URLs from unvalidated scraped content | `7e55f3c` |
| 7 | Unbounded scraper resource usage — no request timeouts, uncapped pagination loops | `f96f9d7` |
| 8 | Minor A05 items — `.dockerignore` misaligned with `.gitignore`, no `server_tokens off` | `f96f9d7` |
| 9 | Weekly scrape cron job silently never ran (CRLF byte handling broke its shell redirection) | `7ca4ee2` |

Checked with no findings during the OWASP pass (2026-08-16): A02 Cryptographic
Failures, A03 Injection (beyond #6), A06 Vulnerable Components, A07 Auth
Failures (no auth surface exists), A08 Software/Data Integrity, A09
Logging/Monitoring, hard-coded secrets, `eval`/`subprocess`/unsafe
deserialization.
