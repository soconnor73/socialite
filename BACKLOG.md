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

## Not backlogged (reviewed, no action needed)

- **Hard-coded secrets** — re-checked with a broader grep across `.py`/`.js`/`.json`/
  `.yml`/`.conf` files; confirms original finding of none found. `.gitignore` already
  excludes `.env` and key/cert files (see recent commit `ca56f4f`).
- **`eval()`/dangerous exec, weak crypto, shell injection** — confirmed absent; also
  checked `scrape_shows.py`/`aggregate_events.py` for `subprocess`/`shell=True`/
  `pickle`/`yaml.load`/`os.system` — none found.
- **`requirements.txt` dependencies** (`beautifulsoup4==4.15.0`, `cloudscraper==1.2.71`)
  — current, no known advisories checked against at time of review.
