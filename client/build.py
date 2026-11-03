"""Build the framework-free Vercel static site; Python standard library only."""
from __future__ import annotations
import html
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'


def env_values(file: Path) -> dict[str, str]:
    result = {}
    if file.is_file():
        for line in file.read_text(encoding='utf-8-sig').splitlines():
            match = re.match(r'^\s*(PUBLIC_[A-Z0-9_]+)\s*=\s*(.*)$', line)
            if match:
                val = match.group(2).strip()
                if val[:1] in ('"', "'") and val[-1:] == val[:1]:
                    val = val[1:-1]
                result[match.group(1)] = val
    return result


def verify_url(name: str, value: str, *, production: bool, origin_only=False) -> str:
    if not value:
        return ''
    u = urlsplit(value)
    if (u.scheme not in ('http','https') or not u.hostname or u.username or u.password or
            any(ch in value for ch in '<>\n\r\t"\'')):
        raise ValueError(f'{name} must be a safe HTTP(S) address without credentials.')
    if production and u.scheme != 'https':
        raise ValueError(f'{name} must use HTTPS in production.')
    if origin_only and (u.path not in ('','/') or u.query or u.fragment):
        raise ValueError(f'{name} must be an origin without a path, query or fragment.')
    return value.rstrip('/')


def build():
    values = {**env_values(ROOT/'.env'), **{k:v for k,v in os.environ.items() if k.startswith('PUBLIC_')}}
    production = os.environ.get('VERCEL') == '1' or os.environ.get('APP_ENV') == 'production'
    api = verify_url('PUBLIC_API_BASE_URL', values.get('PUBLIC_API_BASE_URL',''), production=production)
    if production and api.startswith(('http://localhost','http://127.0.0.1','https://localhost','https://127.0.0.1')):
        raise ValueError('Production API URL cannot point to localhost.')
    site = verify_url('PUBLIC_SITE_URL', values.get('PUBLIC_SITE_URL',''), production=production, origin_only=True)
    key = values.get('PUBLIC_TURNSTILE_SITE_KEY','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{0,150}', key):
        raise ValueError('PUBLIC_TURNSTILE_SITE_KEY has invalid characters.')

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    for dirname in ('styles','scripts','assets','data'):
        shutil.copytree(ROOT/dirname, OUT/dirname, ignore=shutil.ignore_patterns('.*', '*.ttf','*.otf','*.zip', '*.pyc','__pycache__'))
    required = [OUT/'assets/fonts/Inter/inter-latin-variable.woff2', OUT/'assets/fonts/Inter/inter-latin-italic.woff2', OUT/'assets/fonts/Manrope/manrope-latin-variable.woff2']
    if not all(font.is_file() and font.read_bytes()[:4] == b'wOF2' for font in required):
        raise ValueError('The bundled Inter and Manrope WOFF2 files are missing or invalid.')
    public = {'apiBaseUrl':api, 'siteUrl':site, 'turnstileSiteKey':key}
    (OUT/'scripts/config.generated.js').write_text('window.PORTFOLIO_CONFIG = Object.freeze('+json.dumps(public)+');\n', encoding='utf-8')
    index = (ROOT/'index.html').read_text(encoding='utf-8')
    if site:
        index = index.replace('</head>', f'  <link rel="canonical" href="{html.escape(site)}/">\n  <meta property="og:url" content="{html.escape(site)}/">\n</head>', 1)
        index = index.replace('content="/assets/images/mae-ann-1122.webp"', f'content="{html.escape(site)}/assets/images/mae-ann-1122.webp"', 1)
        (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+html.escape(site)+'/</loc></url></urlset>\n',encoding='utf-8')
    (OUT/'index.html').write_text(index, encoding='utf-8')
    (OUT/'404.html').write_bytes((ROOT/'404.html').read_bytes())
    (OUT/'assets/career').mkdir(parents=True,exist_ok=True)
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n'+(f'Sitemap: {site}/sitemap.xml\n' if site else ''),encoding='utf-8')
    print('Frontend build complete: client/dist')
    if not api: print('NOTE: Contact is unavailable until PUBLIC_API_BASE_URL is configured.')
    print('Fonts: Inter and Manrope served locally (no font CDN).')
    return 0

if __name__ == '__main__':
    raise SystemExit(build())
