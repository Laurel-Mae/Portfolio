"""Build one clean, portable development ZIP (with sanitized environment files)."""
from __future__ import annotations
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT.parent/(ROOT.name+'-Python313-Clean.zip')
ROOT_FILES = ('.gitignore','.env','.env.example','start.bat','zip.bat','README.md')
ROOT_FOLDERS = ('client','database','server')
IGNORED_DIRS = {'.git','.venv','venv','__pycache__','.pytest_cache','.vercel','node_modules','dist'}
IGNORED_NAMES = {'config.generated.js','.contact-key','fonts.local.css'}
SKIP_ENDINGS = ('.pyc','.pyo','.log','.db','.db-wal','.db-shm','.sqlite','.sqlite3','.ttf','.otf','.woff','.zip','.tmp','.partial')


def main():
    if sys.version_info[:2] != (3,13):
        raise SystemExit('The packaging helper requires Python 3.13.')
    missing=[str(ROOT/p) for p in (*ROOT_FILES,*ROOT_FOLDERS) if not (ROOT/p).exists()]
    if missing:raise SystemExit('Required paths are missing: '+', '.join(missing))
    if not (ROOT/'client/index.html').is_file() or not (ROOT/'server/main.py').is_file():
        raise SystemExit('The frontend and backend source files are incomplete.')
    entries={}
    for dirname in ROOT_FOLDERS:
        for path in sorted((ROOT/dirname).rglob('*')):
            if not path.is_file():continue
            rel=path.relative_to(ROOT)
            if IGNORED_DIRS.intersection(rel.parts) or any(part.startswith('.venv-') for part in rel.parts):continue
            if path.name in IGNORED_NAMES or path.name=='.env' or path.name.startswith('.env.') and path.name!='.env.example':continue
            if path.name.endswith(SKIP_ENDINGS):continue
            if path.is_symlink():continue
            entries[str(rel).replace('\\','/')]=path.read_bytes()
        # Always ship a SAFE empty-value .env placeholder instead of actual credentials.
        example=ROOT/dirname/'.env.example'
        if example.is_file():entries[f'{dirname}/.env']=example.read_bytes()
    for name in ROOT_FILES:
        entries[name]=(ROOT/'.env.example' if name=='.env' else ROOT/name).read_bytes()
    # Font binaries ship with the source so the portfolio works without Google Fonts.
    required_fonts = ('client/assets/fonts/Inter/inter-latin-variable.woff2',
                      'client/assets/fonts/Inter/inter-latin-italic.woff2',
                      'client/assets/fonts/Manrope/manrope-latin-variable.woff2')
    if not all(path in entries and entries[path].startswith(b'wOF2') for path in required_fonts):
        raise SystemExit('Missing valid local WOFF2 fonts; restore the bundled fonts before packaging.')
    # Include an explicit folder entry so the expected 3 directories are preserved.
    with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as archive:
        for folder in (*ROOT_FOLDERS, 'client/assets/career'):
            archive.writestr(f'{ROOT.name}/{folder}/',b'')
        for name,payload in sorted(entries.items()):
            archive.writestr(f'{ROOT.name}/{name}',payload)
    with zipfile.ZipFile(DEST) as z:
        bad=z.testzip()
        if bad:raise SystemExit('ZIP integrity failed: '+bad)
        top={name.split('/')[1] for name in z.namelist() if len(name.split('/'))>1 and name.split('/')[1]}
        expected=set(ROOT_FILES)|set(ROOT_FOLDERS)
        if top!=expected:raise SystemExit(f'Unexpected ZIP root entries: {top^expected}')
        assert not any(name.endswith('/database.db') for name in z.namelist())
    print('Created:',DEST)
    print('Included:',len(entries),'files; root:',', '.join(ROOT_FOLDERS+ROOT_FILES))
    print('Security: secrets, databases, dependencies and test output omitted.')
    print('Fonts: three locally hosted Inter/Manrope WOFF2 files included.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
