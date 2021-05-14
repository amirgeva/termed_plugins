import os
import json
import subprocess as sp
from typing import List


def scan_headers(item):
    cmd = item.get('command').split()
    try:
        i = cmd.index('-o')
        del cmd[i:i + 2]
    except ValueError:
        pass
    cmd.insert(1, '-MM')
    cp = sp.run(cmd, capture_output=True, cwd=item.get('directory'))
    headers = []
    for line in cp.stdout.split():
        if line.endswith('.h'):
            headers.append(line)
    return headers


def scan_makefile(build_folder: str, path: str):
    source_root = ''
    for line in open(path).readlines():
        if line.startswith('CMAKE_SOURCE_DIR'):
            source_root = line.split()[-1]
            break
    if not source_root:
        return False
    commands_path = os.path.join(build_folder, 'compile_commands.json')
    if not os.path.exists(commands_path):
        return False
    compile_commands = json.load(open(commands_path))
    file_paths = set()
    for item in compile_commands:
        file_paths.add(item.get('file'))
        headers = scan_headers(item)
        for header in headers:
            file_paths.add(header)
    return source_root, file_paths


def paths2tree(source_root: str, file_paths: List[str]):
    root = {}
    for path in file_paths:
        rel = os.path.relpath(path, source_root)
        parts = []
        while rel:
            head, tail = os.path.split(rel)
            parts.append(tail)
            rel = head
        parts = list(reversed(parts))
        cur = root
        for part in parts[0:-1]:
            if part in cur:
                cur = cur.get(part)
            else:
                cur[part] = {}
        cur[parts[-1]] = ''
    return root


def scan_cmake(build_folder: str, path: str):
    source_root = ''
    compile_commands = None
    for line in open(path).readlines():
        if line.startswith('CMAKE_SOURCE_DIR'):
            source_root = line.split()[-1]
            break
    if not source_root:
        return False
    commands_path = os.path.join(build_folder, 'compile_commands.json')
    if not os.path.exists(commands_path):
        return False
    compile_commands = json.load(open(commands_path))
    file_paths = set()
    for item in compile_commands:
        file_paths.add(item.get('file'))
        headers = scan_headers(item)
        for header in headers:
            file_paths.add(header)
    return source_root, paths2tree(file_paths)
