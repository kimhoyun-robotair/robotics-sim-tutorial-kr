"""GPU 없이 문서 연결, Python 문법, 구성 파일과 URDF를 검사한다."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    counts = {"python_files": 0, "python_blocks": 0, "markdown_files": 0,
              "bash_blocks": 0, "relative_links": 0, "lessons": 0, "projects": 0, "config_files": 0}
    roots = [ROOT / n for n in ("docs", "examples", "scripts", "tests", "extensions", "assets", "config", ".github")]
    files = [ROOT / "README.md"] + [p for d in roots for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    for path in files:
        rel = path.relative_to(ROOT)
        try:
            if path.suffix == '.py':
                ast.parse(path.read_text(encoding='utf-8'), filename=str(rel))
                counts['python_files'] += 1
            elif path.suffix == '.md':
                text = path.read_text(encoding='utf-8')
                counts['markdown_files'] += 1
                if len(re.findall(r'^```', text, re.M)) % 2:
                    errors.append(f'{rel}: unclosed code fence')
                for index, code in enumerate(re.findall(r'^```python\s*\n(.*?)^```', text, re.M | re.S), 1):
                    try:
                        ast.parse(code, filename=f'{rel}:python-block-{index}')
                        counts['python_blocks'] += 1
                    except SyntaxError as exc:
                        errors.append(f'{rel}: Python block {index}: {exc}')
                for index, code in enumerate(re.findall(r'^```bash\s*\n(.*?)^```', text, re.M | re.S), 1):
                    result = subprocess.run(['bash', '-n'], input=code, capture_output=True, text=True)
                    counts['bash_blocks'] += 1
                    if result.returncode:
                        errors.append(f'{rel}: Bash block {index}: {result.stderr.strip()}')
                no_code = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M | re.S)
                for target in re.findall(r'\]\(([^\s)]+)\)', no_code):
                    if target.startswith(('https:', 'http:', 'mailto:', '#')):
                        continue
                    target = unquote(target.split('#', 1)[0])
                    if target and not (path.parent / target).resolve().exists():
                        errors.append(f'{rel}: missing link {target}')
                    counts['relative_links'] += 1
            elif path.suffix == '.toml':
                tomllib.loads(path.read_text())
                counts['config_files'] += 1
            elif path.suffix == '.json':
                json.loads(path.read_text())
                counts['config_files'] += 1
            elif path.suffix in ('.yml', '.yaml'):
                import yaml
                yaml.safe_load(path.read_text())
                counts['config_files'] += 1
            elif path.suffix == '.urdf':
                robot = ET.parse(path).getroot()
                links = {link.attrib['name'] for link in robot.findall('link')}
                for link in robot.findall('link'):
                    inertial = link.find('inertial')
                    if inertial is None:
                        raise ValueError(f"{link.attrib['name']}: missing inertia")
                    if float(inertial.find('mass').attrib['value']) <= 0:
                        raise ValueError('mass must be positive')
                    inertia = inertial.find('inertia').attrib
                    import numpy as np
                    tensor = np.array([[float(inertia['ixx']), float(inertia['ixy']), float(inertia['ixz'])],
                                       [float(inertia['ixy']), float(inertia['iyy']), float(inertia['iyz'])],
                                       [float(inertia['ixz']), float(inertia['iyz']), float(inertia['izz'])]])
                    eig = np.linalg.eigvalsh(tensor)
                    if min(eig) <= 0 or max(eig) > sum(eig) - max(eig) + 1e-10:
                        raise ValueError('nonphysical inertia tensor')
                for joint in robot.findall('joint'):
                    if joint.find('parent').attrib['link'] not in links or joint.find('child').attrib['link'] not in links:
                        raise ValueError('joint references missing link')
                counts['config_files'] += 1
        except (SyntaxError, ValueError, OSError, ET.ParseError, KeyError, AttributeError) as exc:
            errors.append(f'{rel}: {exc}')
    lessons = sorted((ROOT / 'docs/lessons').glob('[0-9][0-9]-*.md'))
    numbers = [int(p.name[:2]) for p in lessons]
    counts['lessons'] = len(lessons)
    if numbers != list(range(1, 41)):
        errors.append(f'Expected exactly stages 01..40, found {numbers}')
    project_steps = [9, 15, 17, 22, 27, 33, 36, 38]
    for number in project_steps:
        matching = [p for p in lessons if int(p.name[:2]) == number]
        if len(matching) == 1 and '중간 프로젝트' in matching[0].read_text():
            counts['projects'] += 1
        else:
            errors.append(f'Stage {number}: missing intermediate project')
    for path in lessons:
        body = path.read_text()
        if '```' not in body or 'docs.isaacsim.omniverse.nvidia.com/6.0.1/' not in body:
            errors.append(f'{path.name}: code example or pinned official reference missing')
    return {"status": "PASS" if not errors else "FAIL", "counts": counts, "errors": errors,
            "scope": "static syntax, references and authored URDF structure; no Isaac Sim execution"}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status'] == 'PASS' else 1)
