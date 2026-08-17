# Security Review Report

## Summary
Original audit for hard-coded passwords, secrets, and other common security
vulnerabilities. All findings below were validated and resolved as of
2026-08-16 — see `BACKLOG.md` for the fuller OWASP Top 10 pass that followed,
and its Resolved table for commit references.

## Findings

### 1. Hard-coded Secrets — confirmed, no action needed
No hard-coded passwords, API keys, or secrets found, re-checked with a
broader grep across `.py`/`.js`/`.json`/`.yml`/`.conf` files. `.gitignore`
and `.dockerignore` both exclude `.env`/`*.pem`/`*.key`.

### 2. Cross-Site Scripting (XSS) — ✅ Fixed
The `innerHTML` call sites flagged here were mostly config-driven and safe,
but two did interpolate scraped, untrusted event data (`show.title`,
`show.venue`) directly into markup — a real stored-XSS vector, since that
data comes from 30+ third-party venue scrapers. Fixed by rendering those
fields via `textContent`/DOM properties instead of string-built `innerHTML`.
See `BACKLOG.md` findings #2 and #6.

### 3. Insecure Coding Practices — confirmed, no action needed
No `eval()` or other dangerous execution functions; no weak cryptographic
algorithms found.

## Recommendations status
- **Sanitize inputs** — done (textContent-based rendering, not a sanitizer
  library, since the fix is narrow to specific known fields).
- **Security headers** — done: CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy all added (`BACKLOG.md` #4).
- **Environment variables for secrets** — no secrets exist yet; convention
  is in place (`.gitignore`/`.dockerignore` both exclude `.env`) for if that
  changes.
