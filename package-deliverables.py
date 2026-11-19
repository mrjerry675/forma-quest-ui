"""Bundle browser demos and the native Figma generator, without node_modules."""
from pathlib import Path
import json
import shutil
import subprocess
import zipfile
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parent
license_dir = root / 'vendor' / 'licenses'
license_dir.mkdir(exist_ok=True)
result = subprocess.run(['rg', '--files', '--hidden', '--no-ignore', 'node_modules', '-g', '*LICENSE*', '-g', '*license*', '-g', '*NOTICE*'], cwd=root, capture_output=True, text=True, check=True)
for filename in result.stdout.splitlines():
    source = root / filename
    if source.is_file() and source.suffix.lower() not in {'.js', '.ts', '.map'}:
        label = '__'.join(source.relative_to(root / 'node_modules').parts)
        shutil.copyfile(source, license_dir / label)
(root / 'vendor' / 'THIRD_PARTY.txt').write_text(
    'Browser export libraries: jsPDF 4.2.1 (MIT) and docx 9.16.0 (MIT).\n'
    'Original license notices for these libraries and installed dependency packages\n'
    'are preserved in licenses/. Additional development dependency notices may be\n'
    'included. The complete dependency versions are recorded in package-lock.json.\n'
    'The original library bundles retain their embedded copyright notices.\n', encoding='utf-8')

plugin_zip = root / 'Figma_Prototype_Generator.zip'
with zipfile.ZipFile(plugin_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
    for source in sorted((root / 'figma-plugin').rglob('*')):
        if source.is_file():
            archive.write(source, source.relative_to(root).as_posix())

files = ['index.html', 'resume.html', 'learn.html', 'handoff.html', 'styles.css',
         'common.js', 'resume.js', 'learn.js', 'START_HERE.txt', 'package.json',
         'package-lock.json', 'check-prototypes.cjs', 'check-figma.cjs',
         'browser-validation.json', 'figma-validation.json',
         'Figma_Prototype_Generator.zip', 'package-deliverables.py']
for folder in ['vendor', 'figma-plugin', 'previews']:
    files.extend(str(p.relative_to(root)) for p in (root / folder).rglob('*') if p.is_file())

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                path = urlsplit(value)
                if not path.scheme and not path.netloc and path.path:
                    assert (root / unquote(path.path)).is_file(), f'Broken local link: {value}'

for filename in ['index.html', 'resume.html', 'learn.html', 'handoff.html']:
    Links().feed((root / filename).read_text(encoding='utf-8'))

project_zip = root / 'Forma_Quest_Prototype_Pack.zip'
with zipfile.ZipFile(project_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
    for filename in sorted(set(files)):
        source = root / filename
        archive.write(source, 'Forma_Quest/' + source.relative_to(root).as_posix())
with zipfile.ZipFile(project_zip) as archive:
    assert archive.testzip() is None
    assert 'Forma_Quest/figma-plugin/code.js' in archive.namelist()
    assert not any('/node_modules/' in name for name in archive.namelist())
print(json.dumps({'project_zip':str(project_zip), 'size_bytes':project_zip.stat().st_size,
                  'figma_zip':str(plugin_zip), 'files':len(set(files)), 'local_links':'PASS', 'zip_integrity':'PASS'}, indent=2))
