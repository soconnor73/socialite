# Security Backlog

Prioritized, validated from `SECURITY_REVIEW.md` plus additional issues found while
verifying it against the current codebase (2026-08-16). Each item notes whether it
confirms, revises, or adds to the original review.

## P0 — Critical (FIXED)

### 1. Docker socket mounted into the app container — ✅ Fixed
Removed the `/var/run/docker.sock` volume mount from `docker/docker-compose.yml`.
Details below kept for reference.
**File:** `docker/docker-compose.yml:6`
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```
Not in the original review. Nothing in the app (nginx, cron, scrapers) talks to the
Docker API — grep of the codebase shows no `docker` SDK/CLI usage. The mount appears
to be an unused leftover (possibly copied from a Traefik/Homepage template).

Mounting `docker.sock` is effectively root-equivalent access to the host: any process
in the container that can reach the socket can create a privileged container, mount
the host filesystem, and escape. The `:ro` flag only makes the socket *file* read-only
on the container's filesystem — it does **not** restrict what API calls (including
writes, like creating containers) can be made once connected to the socket. Combined
with finding #2 (stored XSS from scraped data), this raises the ceiling on that bug
from "defaced page" to "host compromise."

**Recommendation:** Remove the volume mount entirely unless a concrete feature needs
it. If Homepage-style container discovery is the goal, that belongs on the
Homepage/Traefik container, not this one.

## P1 — High (FIXED)

### 2. Stored XSS via unsanitized scraped data in `innerHTML` — ✅ Fixed
`createEventCard` now renders the card shell as static `innerHTML` (no scraped
fields inline) and sets `show.venue`, `show.title`, and `subtitleText` afterward via
`textContent`, so scraped markup can no longer execute.

A follow-up review found the same bug in a sibling call site: `renderGrid`
(`app.js`, calendar month view) built each `.grid-event-dot` via a template literal
with `show.title`/`show.venue` interpolated into `data-id` and `title` attributes
inside `innerHTML` — the exact same vector, just in attribute context instead of
text context (e.g. a scraped title containing `"` could break out of the attribute).
Fixed by building each dot with `document.createElement` and setting
`dot.dataset.id`/`dot.title` as DOM properties instead of markup.

Details below kept for reference.

**File:** `app.js:708-724` (`createEventCard`), also `app.js:842-843`
**Confirms and raises severity of** original finding #2 (rated Medium there).

The original review flagged `innerHTML` usage generically and called it "Medium"
risk, conditional on "if any of the data... comes from an untrusted source." That
condition is met: `events/events.json` is produced weekly by 30+ scrapers in
`parsers/` that pull HTML from third-party venue websites (see `scrape_shows.py`,
`aggregate_events.py`). `show.title` and `show.venue` from that pipeline are
interpolated directly into `innerHTML` with no escaping:

```js
card.innerHTML = `
    ...
    <span class="card-venue-badge" ...>${show.venue}</span>
    <h3 class="card-title">${show.title}</h3>
    ...
`;
```

A single scraped event with a title/venue like `<img src=x onerror=alert(1)>` (e.g.
if a venue site is compromised, or a scraper mis-parses attacker-controlled content)
executes arbitrary JS for every visitor of the calendar. This is the single highest-
impact finding in practice since the app has no user accounts to compromise — the
main blast radius is combined with finding #1 (host access via `docker.sock`).

**Recommendation:** Switch `show.title`, `show.venue`, and any other scraped field
rendered into the DOM to `textContent`/`innerText` or `document.createElement`, as
the original review recommended. The other `innerHTML` call sites in `app.js` (category
tree, calendar grid, empty-state messages) are safe today — they only interpolate
static config/derived values — but should still move off `innerHTML` as defense in
depth so a future edit can't accidentally pipe scraped data through them unnoticed.

### 3. `javascript:` URI injection via scraped ticket links — ✅ Fixed
Added an `isSafeHttpUrl()` helper (`app.js`) that parses the URL and only allows
`http:`/`https:` schemes; `show.link` is now checked before being assigned to
`dom.modalTicketsLink.href`, and the link is hidden otherwise. Details below kept
for reference.

**File:** `app.js:842-843`
Not in the original review.
```js
if (show.link) {
    dom.modalTicketsLink.href = show.link;
}
```
`show.link` comes from the same untrusted scraper pipeline as #2 and is assigned
directly to an anchor's `href` with no scheme validation. A scraped value of
`javascript:...` would execute when a user clicks "Tickets" in the event modal.

**Recommendation:** Validate the scheme before assigning (allow only `http:`/`https:`),
or reject/strip the value otherwise.

## P2 — Medium (FIXED)

### 4. Missing security headers — ✅ Fixed
Added `docker/security-headers.conf` (X-Content-Type-Options, X-Frame-Options,
Referrer-Policy, Content-Security-Policy) and `include`d it in both `location`
blocks in `docker/nginx.conf`. It's a separate includable file, not inlined at the
`server` level, because nginx's `add_header` inheritance rule would otherwise have
silently dropped these headers on the `/events/events.json` response — that
location already defines its own `add_header`s (Cache-Control/Pragma/Expires),
which resets inheritance from the parent context for that directive. The Dockerfile
now copies the snippet to `/etc/nginx/security-headers.conf` alongside the main
config.

The CSP allows `'unsafe-inline'` for `style-src` because `app.js` sets inline
`style="..."` attributes via `innerHTML` for category dots/venue badges (values
come from trusted `SOURCE_METADATA`/`CATEGORY_MAP` config, not scraped data — see
finding #2's resolution). It also allow-lists `fonts.googleapis.com`/
`fonts.gstatic.com` since `index.html` loads Google Fonts. `script-src` is
restricted to `'self'` (no inline scripts in the app). Details below kept for
reference.

**File:** `docker/nginx.conf`
**Confirms** original review's recommendation — verified the current config had none
of the suggested headers:
```nginx
location / {
    root /app;
    index index.html;
    try_files $uri $uri/ =404;
}
```
No `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, or
`Referrer-Policy`. A CSP in particular would meaningfully blunt findings #2 and #3
even if the underlying code isn't fixed immediately.

## Round 2 — OWASP Top 10 (2021) pass, 2026-08-16

Follow-up review targeting the categories not explicitly covered above: A01
Broken Access Control, A02 Cryptographic Failures, A03 Injection, A04 Insecure
Design, A05 Security Misconfiguration, A06 Vulnerable/Outdated Components, A07
Auth Failures, A08 Software/Data Integrity, A09 Logging/Monitoring, A10 SSRF.

### 5. Entire source tree + runtime scrape cache publicly served — ✅ Fixed (A01 / A05)
`docker/nginx.conf`'s `location / { root /app; try_files $uri $uri/ =404; }`
had no path/extension restriction. Since `COPY . /app/` puts the whole repo
under that root, and `.dockerignore` only excludes `raw_html/`, `.git`, and
most `*.js`, everything else was publicly downloadable: `/scrape_shows.py`,
`/parsers/*.py`, `/requirements.txt`, `/docker/nginx.conf`,
`/docker/docker-compose.yml`, `/README.md`, `/BACKLOG.md`,
`/SECURITY_REVIEW.md` — full scraper source, infra layout, and this
vulnerability backlog, all one `curl` away. Worse: `raw_html/` is excluded
from the Docker *build*, but the weekly cron job (`docker/cronjob`) writes
cached third-party scrape output into `/app/raw_html/` at **runtime**, and
that directory sat under the same served root — so scraped venue-site HTML/JSON
was being publicly re-hosted too.

Fixed by replacing the catch-all with an explicit allowlist: `location =`
blocks for exactly `/`, `/index.html`, `/index.css`, `/app.js`, and
`/events/events.json`, plus a final `location / { return 404; }` catch-all.
Verified against the real repo with `nginx:stable`: all 5 legitimate paths
(including the `?v=NN` cache-busted query strings `index.html` actually
requests) return `200`; `scrape_shows.py`, `requirements.txt`, `README.md`,
`BACKLOG.md`, `docker/nginx.conf`, `docker/docker-compose.yml`,
`parsers/base.py`, `raw_html/`, and `.git/config` all return `404`.

**File:** `docker/nginx.conf`

### 6. SSRF via unvalidated URLs from scraped third-party content (A10) — ✅ Fixed
**File:** `parsers/mn_united_fc.py:87-100`, `parsers/minneapolis.py:92-97,149-175`

- `mn_united_fc.py` extracted `forgeDAPI`/`leagueForgeDAPIv1` values via regex
  from mnufc.com's page content and used them unvalidated to build URLs
  fetched via `urlopen`. A compromised/tampered upstream response could have
  redirected the scraper to an internal host or a `file://` URL.
- `minneapolis.py` took a scraped `<a href>` verbatim (only rewritten if it
  started with `/`) and passed it straight to `_get_detail_venue()` →
  `urlopen()` with no host allowlist.

Fixed by adding `_is_safe_dapi_base()`/`_is_safe_detail_url()` helpers (same
shape as the `isSafeHttpUrl()` fix already applied in `app.js`) that require
`https:` and an exact host match (`dapi.mnufc.com`/`dapi.mlssoccer.com` for
the first, `www.minneapolis.org` for the second) before a scraped URL is used
as a fetch base; otherwise the code falls back to the hardcoded default
(mn_united_fc.py) or returns no venue (minneapolis.py) instead of fetching.
Also sanitized the `minneapolis.py` cache-slug to `[A-Za-z0-9_-]` only,
closing the (Linux-inert, but still worth removing) backslash gap from
finding #8. Verified with unit tests: legit hosts pass, `http:` downgrade,
cloud-metadata IPs, `file://`, and host-confusion attempts (`evil.com/dapi.mnufc.com`)
all correctly rejected.

### 7. Unbounded scraper resource usage (A04 Insecure Design) — ✅ Fixed
**File:** `scrape_shows.py`, `parsers/mn_united_fc.py`, `parsers/minneapolis.py`,
`parsers/minnesota_twins.py`

No timeout on any `urlopen`/`cloudscraper` call — a slow or hostile upstream
could hang the weekly scrape job indefinitely. Several pagination loops
(`visit_duluth`, `castle_danger_brewery`, `luminary_arts_center`,
`utepils_brewery`, `mpls_parks` in `scrape_shows.py`, plus the match-pagination
loop in `mn_united_fc.py`) trusted a server-supplied `total`/empty-page signal
with no hard cap, unlike `minneapolis` which already capped at `max_pages=100`.

Fixed: added a 30s `REQUEST_TIMEOUT` applied to every `urlopen`/`cloudscraper`
call across `scrape_shows.py` and the three parser files that make their own
requests (`mn_united_fc.py`, `minneapolis.py`, `minnesota_twins.py`); added
`MAX_PAGES_PER_WINDOW = 50` and converted the 5 uncapped `while True:` loops in
`scrape_shows.py` to `while page <= MAX_PAGES_PER_WINDOW:`; added
`MAX_MATCH_PAGES = 200` to cap `mn_united_fc.py`'s match-pagination loop.

### 8. Minor hardening items (A05) — mostly fixed
- **Fixed** — `.dockerignore` now excludes `.env`/`.env.*`/`*.pem`/`*.key`/
  `__pycache__`/`*.pyc`/`result.txt`, matching `.gitignore`. (Already mitigated
  in practice by finding #5's allowlist, but worth keeping the ignore files
  consistent.)
- **Fixed** — `server_tokens off;` added to `docker/nginx.conf`; verified the
  `Server` response header now reads `nginx` with no version number.
- **Partially addressed** — container runs as root; no `USER` directive in
  `docker/Dockerfile`. Confirmed the base `nginx:stable` image's default
  `/etc/nginx/nginx.conf` already sets `user nginx;`, so nginx's *worker*
  processes — which parse and serve all untrusted HTTP requests, the actual
  attack surface — already run unprivileged. Only the nginx master process and
  `cron` remain root, and `cron` only ever runs the fixed, hardcoded scraper
  command (no attacker-influenced trigger). A full non-root migration would
  need cron to run under a non-root user and nginx to bind a non-privileged
  port (which means updating the Traefik `loadbalancer.server.port` label in
  `docker-compose.yml` too) — untestable end-to-end here since Docker image
  builds are blocked by the corporate proxy's SSL interception on `pip
  install`. Added `security_opt: [no-new-privileges:true]` to
  `docker-compose.yml` as a compensating control instead (blocks privilege
  escalation via setuid/setgid binaries if the container is compromised).
- **Intentionally skipped** — SRI on the Google Fonts `<link>` tags in
  `index.html`. Google's font CSS responses vary by `User-Agent` (different
  browsers get different `@font-face` rules/formats), so a fixed SRI hash
  would break font loading for a large fraction of visitors. This is a known
  SRI/Google-Fonts incompatibility, not an oversight — leaving unpinned here
  is the standard trade-off recommended for this specific CDN.
- ~~`minneapolis.py`'s cache-slug regex blocks `/` but not `\` in the matched
  segment~~ — fixed as part of finding #6 (slug now sanitized to
  `[A-Za-z0-9_-]` only).

### Checked, no findings
- **A02 Cryptographic Failures** — TLS terminates at Traefik; no certs/keys
  in-repo; `.gitignore` already excludes `*.pem`/`*.key`.
- **A03 Injection (beyond #6/#8)** — no `subprocess`/`os.system`/`eval`/
  `exec`/`pickle`/unsafe `yaml.load`/XML parsing anywhere in `*.py`.
- **A06 Vulnerable Components** — `beautifulsoup4==4.15.0`/`cloudscraper==1.2.71`
  have no known CVEs as of this review; no CDN-loaded `<script>` (only
  CSS-only Google Fonts links, no SRI but limited blast radius).
- **A07 Auth Failures** — confirmed no auth surface exists anywhere in the
  app; the `localStorage`-based "Interested" save feature is appropriate for
  a single-user, no-login app and isn't a partial/insecure auth mechanism.
  Saved events read back from `localStorage` flow through the same
  `textContent`-based safe rendering path as fresh scraped data (see finding
  #2's fix) — no new XSS route via that round-trip.
- **A08 Software/Data Integrity** — dependencies pinned, no unsafe
  deserialization or remote code execution.
- **A09 Logging/Monitoring** — acceptable for this app's scale; noted only
  that scrape failures currently rely on `docker logs` with no alerting, and
  finding #6's `print(f"...{club_dapi_base}")` logs an attacker-influenced
  string unsanitized (minor CRLF log-injection risk, not otherwise actionable).

## Not backlogged (reviewed, no action needed)

- **Hard-coded secrets** — re-checked with a broader grep across `.py`/`.js`/`.json`/
  `.yml`/`.conf` files; confirms original finding of none found. `.gitignore` already
  excludes `.env` and key/cert files (see recent commit `ca56f4f`).
- **`eval()`/dangerous exec, weak crypto, shell injection** — confirmed absent; also
  checked `scrape_shows.py`/`aggregate_events.py` for `subprocess`/`shell=True`/
  `pickle`/`yaml.load`/`os.system` — none found.
- **`requirements.txt` dependencies** (`beautifulsoup4==4.15.0`, `cloudscraper==1.2.71`)
  — current, no known advisories checked against at time of review.
