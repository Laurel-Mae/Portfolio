# Mae Ann Laurel — Portfolio

**Updated November 3, 2026 · Python 3.13 · HTML, CSS, and vanilla JavaScript**

A mobile-first, single-page professional portfolio focused on Networking and IT Support. The design uses Charcoal/Ivory themes, **six desktop header links**, a mobile-only circular section menu, a custom local M/network logo, local Inter/Manrope fonts, editable portfolio data, and a small FastAPI email contact service with ordered SMTP failover.

## Source layout

Only these nine entries are stored at the project root:

```text
anyang/
├── client/          # HTML, CSS, JS, public data, SVG, WOFF2, images, career PDFs
├── server/          # Python FastAPI, SMTP, database access, packaging helpers
├── database/        # SQLite and PostgreSQL schemas (never ship database.db)
├── .gitignore
├── .env             # Nonsecret local defaults; never commit real secrets
├── .env.example
├── start.bat
├── zip.bat
└── README.md
```

## Quick start (Windows)

1. Extract the ZIP **into a new folder**, without merging an old `.venv`, test output, or caches.
2. Open PowerShell inside `anyang`.
3. Run:

```powershell
py -3.13 --version
.\start.bat
```

- Frontend: **http://127.0.0.1:3000**
- Backend health: **http://127.0.0.1:8000/api/health**

The launcher explicitly selects Python **3.13**, creates a private environment at `server/.venv`, and starts the frontend first. If `pip` cannot install backend dependencies, the frontend still loads; contact email delivery remains unavailable. Press **Ctrl+C** to stop processes started by the launcher.

For frontend-only development, use:

```powershell
.\start.bat --frontend-only
```

VS Code: **Python: Select Interpreter → Enter interpreter path →** `anyang\server\.venv\Scripts\python.exe`. Your system default may remain Python 3.14.

## Editable information

No admin panel or frontend framework is needed. **Changes to the JS content modules take effect on page reload.**

| File | What to edit |
|---|---|
| `client/data/profile.js` | Name, role, `identity.status` (student/graduate/current accurate role), hero introduction, portrait caption/subtitle, WhatsApp, email, phone, Resume/CV filenames, developer credit |
| `client/data/experience.js` | Real internships, professional experience, practical training, and responsibilities. A commented example is included. |
| `client/data/education.js` | Real school, program, dates, educational details. A commented example is included. |
| `client/data/skills.js` | Interest areas; verify competence before claiming a skill is demonstrated. |

**Important:** The HTML contains default content for search indexing and browsers without JavaScript. For material changes to identity or claims, also review the fallback content and SEO description in `client/index.html`. Never publish made-up work experience, qualifications, addresses, or certifications.

### When Mae Ann graduates or changes careers

In `client/data/profile.js` you can edit:

```js
identity: {
  name: 'Mae Ann Laurel',
  title: 'Networking & IT Support',
  status: 'IT Graduate', // Example only: use an accurate status.
},
portrait: {
  caption: 'The person behind the work.',
  subtitle: '', // Empty automatically displays Name · identity.status.
},
```

You can override `portrait.subtitle` with your own exact wording. The same file controls introductory text and the displayed title. When updating roles or status, also update descriptions that refer to being a student, and review the static SEO fallback in the HTML.

### Career Profile PDFs

Put the real document files in:

```text
client/assets/career/
├── Mae-Ann-Laurel-Resume.pdf
└── Mae-Ann-Laurel-CV.pdf
```

Keep the filenames synchronized with `client/data/profile.js`:

```js
documents: {
  resume: { title: 'Resume', filename: 'Mae-Ann-Laurel-Resume.pdf' },
  cv: { title: 'Curriculum Vitae', filename: 'Mae-Ann-Laurel-CV.pdf' },
},
```

No URLs are entered. The UI checks whether each PDF actually exists, shows **Preview/Download** when present and **Not yet available** when missing. PDF previews use the browser's built-in viewer. The PDF filenames may contain letters, numbers, dots, hyphens, and underscores; path separators are not permitted.

### Contact details and WhatsApp

Set public fields in `profile.contact`:

```js
contact: {
  email: 'approved-public-email@example.com',
  whatsapp: '+639XXXXXXXXX', // Example format; replace with the actual number.
  phone: '',                  // Optional.
},
```

WhatsApp uses `https://wa.me/<digits>`; it appears only for a valid 8–15-digit international number. Empty contact fields are hidden rather than filled with invented details. LinkedIn is not a default profile field.

## Navigation and interaction

- **Wide desktop (over 1080px):** `M logo | Name / Networking & IT Support` on the left; Home, About, Experience, Education, Skills, Contact in the center; Career Profile CTA and icon-only Light/Dark toggle on the right. No floating orbit button.
- **1080px and below:** Full navigation switches to a bottom-right AssistiveTouch-style circular menu. The header retains identity, Career Profile, and theme switch.
- Both navigation systems track the current section. Anchor destinations land just below the sticky header, not behind excessive section padding. The mobile footer is compact without the former 110px blank strip.
- Built-in accessibility: reduced motion, keyboard navigation, dialog focus management, and contrast-conscious light/dark tokens.
- Custom toast, tooltip, modal, dropdown, mobile menu, loading indicator, skeleton, spinner, and scrollbar.
- Loader is triggered only when the main portrait takes noticeably long to load; no artificial waiting screen.

## Font and brand assets

**Inter** (body) and **Manrope** (headings) are included as three local WOFF2 files:

```text
client/assets/fonts/Inter/inter-latin-variable.woff2
client/assets/fonts/Inter/inter-latin-italic.woff2
client/assets/fonts/Manrope/manrope-latin-variable.woff2
```

Their OFL license files are included. **No Google Fonts/CDN connection is needed.** If fonts are removed, the launcher supports `start.bat --fonts-only` to attempt restoring them from Google Fonts; otherwise the browser falls back to system sans-serif fonts. The final `zip.bat` package always requires and includes the local WOFF2 files.

The custom scalable M/network mark is saved at `client/assets/icons/network-m.svg` and also used for the favicon.

## Environment and deployment

The ZIP includes **sanitized** root, client and server `.env` placeholders and matching `.env.example` files:

- `/.env`: local development hosts and ports (`PYTHON_VERSION=3.13`).
- `/client/.env`: public API URL, public site URL and optional Turnstile **site** key.
- `/server/.env`: private SMTP accounts/passwords, email recipient, database driver and security options.

The backend reads the server secrets. The browser reads only `client/scripts/config.generated.js` generated with public settings. Never commit real `.env` values, generated local databases, or service tokens.

### SMTP account failover

Configure `server/.env` after extraction:

```dotenv
CONTACT_TO=owner@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USER=account1@example.com,account2@example.com,account3@example.com
SMTP_PASS=app_password_1,app_password_2,app_password_3
```

This is example configuration, **not active credentials**. User/password positions must match. For credentials containing commas or senders with differing connection parameters, use `SMTP_ACCOUNTS_JSON` (documented in `server/.env.example`). The sender account is separate from the portfolio owner's inbox; the visitor's validated address becomes `Reply-To`.

The service attempts the next SMTP account only after a confirmed failure, and stops on server acceptance. It does **not** blindly retry an uncertain send. SMTP acceptance does not guarantee inbox delivery. The contact form reports that email delivery is unavailable until real SMTP/recipient settings are provided.

### Database

The contact API uses SQLite during development (`database/schema.sql`), with a PostgreSQL schema for future Supabase production (`database/schema.postgres.sql`). It records only delivery references, keyed fingerprints and rate-limit records, not message bodies. Production needs a **shared persistent database** for idempotency and rate limits. Keep the private `CONTACT_HMAC_KEY` configured and do not expose the database connection string to the browser.

### Hosting

- **Vercel frontend:** set Root Directory to `client`. It runs `python3 build.py` (Python standard library only) and serves `dist/`. Set `PUBLIC_API_BASE_URL` to the deployed HTTPS backend endpoint.
- **Backend:** deploy `server/` to a Python-capable service, using `server.main:app` (or `main:app` when `server/` is the project root). Set environment variables in the provider's secret settings. Check Python 3.13 support and exact port behavior with your provider.
- Render Free blocks standard outgoing SMTP ports. Use a service/environment that supports the configured provider or switch to an HTTPS email API in a future update.
- The custom `404.html` is available in the static output. Local development responds with a **404 status** for missing pages; deployed routing must likewise serve a 404 status for unknown routes.

## Build and package

Run `zip.bat` from the project root. It uses Python 3.13 and creates a ZIP in the parent folder.

The ZIP includes the actual local fonts, SVG mark, optimized portraits, Python and frontend source, database schemas, safe `.env` placeholders, and empty `client/assets/career/` folder for future PDFs. It excludes actual secrets, local databases and HMAC keys, `.venv`, caches, tests, generated config files, and temporary output.

Do not place real private documents in `client/assets/career/`; all files there are public when deployed.

## Troubleshooting

| Symptom | Check |
|---|---|
| Backend unavailable / pip error | Run `py -3.13 --version`; verify DNS to PyPI and `server/.venv` imports. Frontend remains usable. |
| VS Code displays Python 3.14 | Explicitly choose `server/.venv/Scripts/python.exe` for this workspace. |
| Contact form says unavailable | Set valid `CONTACT_TO` + SMTP settings in `server/.env`; verify backend `/api/health` and `/api/contact/status`. |
| Career document not yet available | Confirm the exact PDF filename in `client/assets/career/` matches `profile.js`. |
| Fonts appear as system defaults | Confirm all three WOFF2 files exist and are accessible under `/assets/fonts/`. |
| Footer or header changed unexpectedly | Hard-refresh after deploying; check responsive styles and static host caching. |
| Bad URL displays 404 | Expected; use **Return to portfolio**. |
