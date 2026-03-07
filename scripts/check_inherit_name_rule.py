#!/usr/bin/env python3
"""Validate `_inherit` / `_name` convention for addon component classes.

Rule:
- When a class extends an existing component via `_inherit`, it must not define
  a different `_name` unless it is a true duplication case.

Current policy implemented by this checker:
- `_inherit` present + `_name` present + `_name != _inherit` => violation.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    class_name: str
    inherit_value: str
    name_value: str


def _iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        normalized = str(path).replace('\\', '/')
        if '/tests/' in normalized or '/__pycache__/' in normalized:
            continue
        yield path


def _literal_str(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    return None


def _class_attrs(node: ast.ClassDef) -> tuple[str | None, str | None]:
    inherit_value = None
    name_value = None
    for stmt in node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        value = _literal_str(stmt.value)
        if value is None:
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == '_inherit':
                inherit_value = value
            elif isinstance(target, ast.Name) and target.id == '_name':
                name_value = value
    return inherit_value, name_value


def find_violations(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in _iter_python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            inherit_value, name_value = _class_attrs(node)
            if not inherit_value or not name_value:
                continue
            if name_value != inherit_value:
                violations.append(
                    Violation(
                        path=path,
                        line=node.lineno,
                        class_name=node.name,
                        inherit_value=inherit_value,
                        name_value=name_value,
                    )
                )

    violations.sort(key=lambda v: (str(v.path), v.line, v.class_name))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check that extension classes do not redefine a different _name when using _inherit.'
    )
    parser.add_argument(
        '--root',
        default='src/gtimelog/addons',
        help='Root directory to scan (default: src/gtimelog/addons).',
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f'[ERROR] Path not found: {root}')
        return 2

    violations = find_violations(root)
    if not violations:
        print('[OK] No _inherit/_name convention violations found.')
        return 0

    print('[FAIL] _inherit/_name convention violations detected:')
    for violation in violations:
        rel_path = violation.path.as_posix()
        print(
            f'  - {rel_path}:{violation.line} {violation.class_name} '
            f'(_inherit={violation.inherit_value!r}, _name={violation.name_value!r})'
        )
    print(f'Total violations: {len(violations)}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
