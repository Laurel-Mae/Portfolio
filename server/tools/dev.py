"""Windows-friendly Python 3.13 launcher. Frontend has no third-party dependencies."""
from __future__ import annotations
import argparse
import functools
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'client'
SERVER = ROOT / 'server'
VENV = SERVER / '.venv'
PYTHON = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def read_env(path: Path):
    values = {}
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match = re.match(r'^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*)$',line)
            if match:
                value = match.group(2).strip()
                if value[:1] in ('"',"'") and value[-1:] == value[:1]: value = value[1:-1]
                values[match.group(1)] = value
    return values


def ensure_local_config():
    for relative in ('.env','client/.env','server/.env'):
        target = ROOT/relative
        if not target.is_file():
            shutil.copyfile(ROOT/(relative+'.example'),target)
            print('Created safe configuration:',relative,flush=True)


def safe_address(addr):
    if addr not in {'127.0.0.1','localhost','::1'}:
        raise ValueError('Development binds only to localhost. Change public deployment settings separately.')
    return addr


def safe_port(value):
    n = int(value)
    if not (1024 <= n < 65536): raise ValueError('Development ports must be between 1024 and 65535.')
    return n


class StaticHandler(SimpleHTTPRequestHandler):
    def do_GET(self): self.safe_request(super().do_GET)
    def do_HEAD(self): self.safe_request(super().do_HEAD)
    def safe_request(self, callback):
        parts = unquote(urlsplit(self.path).path).split('/')
        if any(p.startswith('.') or p in {'dist','vercel.json','build.py'} for p in parts if p):
            self.send_error(404); return
        suffix = Path(parts[-1]).suffix.lower()
        if suffix in {'.env','.py','.bat','.sql','.db','.toml','.md','.txt'}:
            self.send_error(404); return
        return callback()
    def list_directory(self, path):
        self.send_error(404); return None
    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = CLIENT / '404.html'
            if page.is_file():
                payload = page.read_bytes()
                self.send_response(404)
                self.send_header('Content-Type','text/html; charset=utf-8')
                self.send_header('Content-Length',str(len(payload)))
                self.end_headers()
                if self.command != 'HEAD': self.wfile.write(payload)
                return
        return super().send_error(code,message,explain)
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        super().end_headers()


FONT_CSS_URL = ('https://fonts.googleapis.com/css2?'
                'family=Inter:ital,wght@0,100..900;1,100..900&'
                'family=Manrope:wght@200..800&display=swap')
FONTS = {
    ('Inter','normal'):('Inter','inter-latin-variable.woff2','InterOffline'),
    ('Inter','italic'):('Inter','inter-latin-italic.woff2','InterOffline'),
    ('Manrope','normal'):('Manrope','manrope-latin-variable.woff2','ManropeOffline'),
}


def try_install_fonts():
    """Optional recovery of the bundled local WOFF2 files on the user's computer."""
    local_css = CLIENT/'styles/fonts.css'
    if all((CLIENT/'assets/fonts'/folder/filename).is_file() for folder,filename,_ in FONTS.values()):
        print('Local Inter and Manrope fonts already available.',flush=True)
        return True
    try:
        headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
        css = urllib.request.urlopen(urllib.request.Request(FONT_CSS_URL, headers=headers),timeout=5).read().decode('utf-8')
        selected = {}
        for block in re.findall(r'/\*\s*latin\s*\*/\s*(@font-face\s*\{.*?\})',css,re.S):
            family = re.search(r"font-family:\s*['\"]?([\w -]+)",block)
            style = re.search(r'font-style:\s*(normal|italic)',block)
            url = re.search(r'url\((https://[^)]+\.woff2)\)',block)
            if family and style and url and (family.group(1),style.group(1)) in FONTS:
                selected[(family.group(1),style.group(1))] = url.group(1)
        if len(selected)!=3:
            raise ValueError('The Google Fonts response did not contain all three WOFF2 variants.')
        # Never fetch from an arbitrary origin if the stylesheet response changes.
        for key,url in selected.items():
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme!='https' or parsed.hostname!='fonts.gstatic.com':
                raise ValueError('Unexpected font download host.')
            data = urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=6).read(2000001)
            if not data.startswith(b'wOF2') or len(data)>2000000:
                raise ValueError('Unexpected font data format or size.')
            family,filename,_ = FONTS[key]
            output = CLIENT/'assets/fonts'/family/filename
            output.parent.mkdir(parents=True,exist_ok=True)
            temp=output.with_suffix('.partial')
            temp.write_bytes(data)
            temp.replace(output)
        # fonts.css already references self-hosted WOFF2 files. No stylesheet rewrite needed.
        print('Installed local Inter and Manrope WOFF2 files (3 variants).',flush=True)
        return True
    except Exception as exc:
        print(f'Local font fetch unavailable ({type(exc).__name__}); system fonts will be used if local WOFF2 files are missing.',flush=True)
        return False


def version_ready():
    if not PYTHON.is_file():return False
    verify='import sys; from importlib import metadata as m; assert sys.version_info[:2]==(3,13); assert sys.prefix!=sys.base_prefix; '
    pins=re.findall(r'^([A-Za-z][\w-]*)(?:\[[^]]+\])?==([^\s#]+)',(SERVER/'requirements.txt').read_text(),re.M)
    for name,version in pins:
        verify+=f'assert m.version({name!r})=={version!r}; '
    verify+='import fastapi, uvicorn, pydantic, email_validator, dotenv, httpx, psycopg; '
    proc=subprocess.run([str(PYTHON),'-c',verify],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return proc.returncode==0


def prepare_environment(*, allow_install, on_pip=None):
    if PYTHON.is_file():
        check=subprocess.run([str(PYTHON),'-c','import sys; assert sys.version_info[:2]==(3,13) and sys.prefix!=sys.base_prefix'],capture_output=True)
        if check.returncode:
            archive=SERVER/('.venv-incompatible-'+str(int(time.time())))
            VENV.rename(archive)
            print(f'Moved incompatible virtual environment to {archive.name}.',flush=True)
    if VENV.is_dir() and not PYTHON.is_file():
        archive=SERVER/('.venv-incomplete-'+str(int(time.time())))
        VENV.rename(archive)
        print(f'Moved incomplete virtual environment to {archive.name}.',flush=True)
    if not PYTHON.is_file():
        print('Creating isolated Python 3.13 virtual environment...',flush=True)
        created=subprocess.run([sys.executable,'-m','venv',str(VENV)])
        if created.returncode:return False
    if version_ready():
        print('Backend dependencies already match the pinned requirements.',flush=True)
        return True
    if not allow_install:
        print('Backend dependencies are missing or outdated. Re-run without --no-install.',flush=True)
        return False
    print('Installing pinned backend dependencies (frontend remains available)...',flush=True)
    cmd=[str(PYTHON),'-m','pip','install','--disable-pip-version-check','--retries','1','--timeout','8','-r',str(SERVER/'requirements.txt')]
    proc=subprocess.Popen(cmd,cwd=str(ROOT))
    if on_pip:on_pip(proc)
    try:
        status=proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait();print('pip timed out after 180 seconds.',flush=True);return False
    if status!=0:
        print('Backend unavailable: dependency installation failed (network/DNS or package index).',flush=True)
        return False
    if not version_ready():
        print('Backend dependency verification failed after installation.',flush=True)
        return False
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend-only',action='store_true',help='Serve the HTML/CSS/JS without running FastAPI.')
    parser.add_argument('--no-install',action='store_true',help='Do not install missing backend packages.')
    parser.add_argument('--no-font-download',action='store_true',help='Use Google Fonts without fetching local WOFF2.')
    parser.add_argument('--fonts-only',action='store_true',help='Try downloading the three local fonts and exit.')
    parser.add_argument('--no-browser',action='store_true',help='Do not automatically open a browser.')
    args=parser.parse_args()
    if sys.version_info[:2] != (3,13):
        print('Python 3.13 required; current interpreter:',sys.version.split()[0]);return 1
    ensure_local_config()
    if args.fonts_only:
        return 0 if try_install_fonts() else 1
    root_env=read_env(ROOT/'.env')
    client_env=read_env(CLIENT/'.env')
    host=safe_address(root_env.get('CLIENT_HOST','127.0.0.1'))
    port=safe_port(root_env.get('CLIENT_PORT','3000'))
    server_host=safe_address(root_env.get('SERVER_HOST','127.0.0.1'))
    server_port=safe_port(root_env.get('SERVER_PORT','8000'))
    base=client_env.get('PUBLIC_API_BASE_URL','')
    if not base or base in {'http://127.0.0.1:8000','http://localhost:8000'}:
        base=f'http://{server_host}:{server_port}'
    u=urlsplit(base)
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:
        raise ValueError('Invalid PUBLIC_API_BASE_URL in client/.env.')
    config={'apiBaseUrl':base.rstrip('/'), 'siteUrl':client_env.get('PUBLIC_SITE_URL',''),
            'turnstileSiteKey':client_env.get('PUBLIC_TURNSTILE_SITE_KEY','')}
    (CLIENT/'scripts/config.generated.js').write_text('window.PORTFOLIO_CONFIG = Object.freeze('+json.dumps(config)+');\n',encoding='utf-8')
    # Binding the port also checks it; never kill a preexisting process.
    try:
        server=ThreadingHTTPServer((host,port),functools.partial(StaticHandler,directory=str(CLIENT)))
    except OSError as e:
        print(f'Frontend port {port} on {host} is unavailable: {e}');return 1
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    print(f'\nFrontend running: http://{host}:{port}',flush=True)
    print('Frontend does not depend on FastAPI, pip, or network connectivity.',flush=True)
    if not args.no_browser:
        try:webbrowser.open(f'http://{host}:{port}')
        except Exception:pass
    backend=None
    pip=None
    try:
        if not args.no_font_download:
            if not all((CLIENT/'assets/fonts'/folder/filename).is_file() for folder,filename,_ in FONTS.values()):
                threading.Thread(target=try_install_fonts,daemon=True).start()
        if not args.frontend_only:
            if prepare_environment(allow_install=not args.no_install,on_pip=lambda proc: None):
                # Never overwrite settings deliberately provided by the user.
                env=os.environ.copy()
                values=read_env(SERVER/'.env')
                if values.get('ALLOWED_ORIGINS','') in ('','http://127.0.0.1:3000,http://localhost:3000'):
                    env.setdefault('ALLOWED_ORIGINS',f'http://{host}:{port},http://localhost:{port}')
                with socket.socket() as check:
                    try:check.bind((server_host,server_port))
                    except OSError:
                        print(f'Backend port {server_port} unavailable. Frontend remains running.',flush=True)
                    else:
                        backend=subprocess.Popen([str(PYTHON),'-m','uvicorn','server.main:app','--host',server_host,
                                                  '--port',str(server_port),'--no-proxy-headers'],cwd=str(ROOT),env=env)
                        print(f'Backend starting: http://{server_host}:{server_port}/api/health',flush=True)
            else:
                print('Contact API is offline; the portfolio is still available.',flush=True)
        print('Press Ctrl+C to stop services started by this launcher.\n',flush=True)
        while True:
            if backend and backend.poll() is not None:
                print(f'Backend stopped (exit {backend.returncode}); frontend still running.',flush=True)
                backend=None
            time.sleep(.35)
    except KeyboardInterrupt:
        print('\nStopping portfolio services...',flush=True)
        return 0
    finally:
        server.shutdown();server.server_close()
        if backend and backend.poll() is None:
            backend.terminate()
            try:backend.wait(timeout=4)
            except subprocess.TimeoutExpired:backend.kill()

if __name__=='__main__':
    raise SystemExit(main())
