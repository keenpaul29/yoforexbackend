#!/usr/bin/env python3
import os, sys, ast, importlib.util, importlib

packages = set()
# Determine standard library directory
stdlib_dir = os.path.dirname(os.path.dirname(importlib.__file__))

for dirpath, dirnames, filenames in os.walk('.'):
    # Skip virtualenvs and cache dirs
    if any(ignored in dirpath for ignored in ('venv', '.venv', 'env', '__pycache__')):
        continue
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                tree = ast.parse(f.read(), filename=path)
        except Exception as e:
            print(f"Skipping {path}: {e}", file=sys.stderr)
            continue
        for node in ast.walk(tree):
            pkg = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split('.')[0]
                    # Process each imported pkg
                    if pkg:
                        # Skip builtins
                        if pkg in sys.builtin_module_names:
                            continue
                        # Detect stdlib
                        spec = importlib.util.find_spec(pkg)
                        if spec and spec.origin and os.path.abspath(spec.origin).startswith(os.path.abspath(stdlib_dir)):
                            continue
                        packages.add(pkg)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    pkg = node.module.split('.')[0]
                    if pkg:
                        if pkg in sys.builtin_module_names:
                            continue
                        spec = importlib.util.find_spec(pkg)
                        if spec and spec.origin and os.path.abspath(spec.origin).startswith(os.path.abspath(stdlib_dir)):
                            continue
                        packages.add(pkg)

# Write out requirements.txt
with open('requirements.txt', 'w') as out:
    for pkg in sorted(packages):
        out.write(pkg + '\n')

print(f"Found {len(packages)} packages. requirements.txt written.")