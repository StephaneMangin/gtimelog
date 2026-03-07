#!/usr/bin/env python3

from __future__ import annotations

import ast
import sys
from pathlib import Path


ALLOWED_MODULE_TYPES = {"technical", "functional"}
ALLOWED_LAYERS = {"platform", "ui", "feature", "integration"}
ALLOWED_LAYER_DEPENDENCIES = {
    "platform": {"platform"},
    "ui": {"platform", "ui"},
    "feature": {"platform", "feature", "ui"},
    "integration": {"platform", "feature", "integration"},
}


class ModuleArchitectureChecker:
    """Validate addon metadata, dependency graph, and layer constraints."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.addons_dir = root_dir / 'src' / 'gtimelog' / 'addons'

    def load_manifests(self):
        manifests = {}
        errors = []

        for manifest_path in sorted(self.addons_dir.glob('*/__manifest__.py')):
            module_name = manifest_path.parent.name
            try:
                content = manifest_path.read_text(encoding='utf-8')
                manifest = ast.literal_eval(content)
            except Exception as exc:
                errors.append(
                    f'{module_name}: impossible de parser {manifest_path} ({exc})'
                )
                continue

            if not isinstance(manifest, dict):
                errors.append(f'{module_name}: le manifest doit être un dict')
                continue

            manifests[module_name] = manifest

        return manifests, errors

    @staticmethod
    def validate_manifest_fields(module_name: str, manifest: dict):
        errors = []

        required_fields = ('module_type', 'layer', 'domain', 'depends')
        for field in required_fields:
            if field not in manifest:
                errors.append(f'{module_name}: champ requis manquant: {field}')

        module_type = manifest.get('module_type')
        if 'module_type' in manifest and module_type not in ALLOWED_MODULE_TYPES:
            errors.append(
                f'{module_name}: module_type invalide: {module_type!r} '
                f'(attendu: {sorted(ALLOWED_MODULE_TYPES)})'
            )

        layer = manifest.get('layer')
        if 'layer' in manifest and layer not in ALLOWED_LAYERS:
            errors.append(
                f'{module_name}: layer invalide: {layer!r} '
                f'(attendu: {sorted(ALLOWED_LAYERS)})'
            )

        domain = manifest.get('domain')
        if 'domain' in manifest:
            if not isinstance(domain, str) or not domain.strip():
                errors.append(f'{module_name}: domain doit être une chaîne non vide')

        depends = manifest.get('depends')
        if 'depends' in manifest and not isinstance(depends, list):
            errors.append(f'{module_name}: depends doit être une liste')

        return errors

    @staticmethod
    def find_cycles(graph: dict[str, list[str]]):
        states = {node: 0 for node in graph}
        stack = []
        cycles = set()

        def normalize_cycle(cycle_nodes):
            body = cycle_nodes[:-1]
            if not body:
                return tuple(cycle_nodes)
            rotations = [tuple(body[i:] + body[:i]) for i in range(len(body))]
            best = min(rotations)
            return best + (best[0],)

        def dfs(node):
            states[node] = 1
            stack.append(node)

            for neighbor in graph[node]:
                if states.get(neighbor, 0) == 0:
                    dfs(neighbor)
                elif states[neighbor] == 1:
                    cycle_start = stack.index(neighbor)
                    cycle_nodes = stack[cycle_start:] + [neighbor]
                    cycles.add(normalize_cycle(cycle_nodes))

            stack.pop()
            states[node] = 2

        for node in graph:
            if states[node] == 0:
                dfs(node)

        return sorted(cycles)

    @staticmethod
    def is_empty_or_docstring_only_init(py_file: Path):
        if py_file.name != '__init__.py':
            return False
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except Exception:
            return False

        body = tree.body
        if not body:
            return True

        if len(body) != 1:
            return False

        node = body[0]
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )

    def check_forbidden_gi_imports(self):
        errors = []
        layer_dirs = [
            self.root_dir / 'src' / 'gtimelog' / 'domain',
            self.root_dir / 'src' / 'gtimelog' / 'application',
        ]

        for layer_dir in layer_dirs:
            if not layer_dir.exists():
                continue

            for py_file in sorted(layer_dir.rglob('*.py')):
                if self.is_empty_or_docstring_only_init(py_file):
                    continue

                try:
                    tree = ast.parse(py_file.read_text(encoding='utf-8'))
                except Exception as exc:
                    rel_path = py_file.relative_to(self.root_dir)
                    errors.append(f'{rel_path}: impossible de parser le fichier ({exc})')
                    continue

                rel_path = py_file.relative_to(self.root_dir)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == 'gi' or alias.name.startswith('gi.repository'):
                                errors.append(
                                    f"{rel_path}: import interdit '{alias.name}' "
                                    'dans domain/application'
                                )
                            if alias.name.startswith('gtimelog.addons'):
                                errors.append(
                                    f"{rel_path}: import addon interdit '{alias.name}' "
                                    'dans domain/application'
                                )
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        if module == 'gi' or module.startswith('gi.repository'):
                            errors.append(
                                f"{rel_path}: import interdit depuis '{module}' "
                                'dans domain/application'
                            )
                        if module.startswith('gtimelog.addons'):
                            errors.append(
                                f"{rel_path}: import addon interdit depuis '{module}' "
                                'dans domain/application'
                            )

        return errors

    def run(self):
        manifests, errors = self.load_manifests()

        for module_name, manifest in manifests.items():
            errors.extend(self.validate_manifest_fields(module_name, manifest))

        for module_name, manifest in manifests.items():
            depends = manifest.get('depends')
            if not isinstance(depends, list):
                continue

            for dep in depends:
                if not isinstance(dep, str) or not dep:
                    errors.append(f'{module_name}: dépendance invalide: {dep!r}')
                    continue
                if dep not in manifests:
                    errors.append(f'{module_name}: dépendance inconnue: {dep}')

        for module_name, manifest in manifests.items():
            depends = manifest.get('depends')
            source_layer = manifest.get('layer')
            source_type = manifest.get('module_type')

            if not isinstance(depends, list):
                continue
            if source_layer not in ALLOWED_LAYER_DEPENDENCIES:
                continue

            allowed_layers = ALLOWED_LAYER_DEPENDENCIES[source_layer]
            for dep in depends:
                if not isinstance(dep, str):
                    continue
                dep_manifest = manifests.get(dep)
                if dep_manifest is None:
                    continue

                dep_layer = dep_manifest.get('layer')
                dep_type = dep_manifest.get('module_type')

                if dep_layer in ALLOWED_LAYERS and dep_layer not in allowed_layers:
                    errors.append(
                        f'{module_name}: règle layer violée ({source_layer} -> {dep_layer}) '
                        f'via dépendance {dep}'
                    )

                if source_type == 'technical' and dep_type == 'functional':
                    errors.append(
                        f'{module_name}: règle type violée (technical -> functional) '
                        f'via dépendance {dep}'
                    )

        graph = {}
        for module_name, manifest in manifests.items():
            depends = manifest.get('depends')
            if not isinstance(depends, list):
                graph[module_name] = []
                continue
            graph[module_name] = [dep for dep in depends if isinstance(dep, str) and dep in manifests]

        cycles = self.find_cycles(graph)
        for cycle in cycles:
            errors.append(f"cycle détecté: {' -> '.join(cycle)}")

        errors.extend(self.check_forbidden_gi_imports())

        if not errors:
            print(f'OK: architecture modulaire valide ({len(manifests)} modules)')
            return 0

        print(f'FAIL: architecture modulaire invalide ({len(errors)} erreur(s))')
        for error in sorted(errors):
            print(f'- {error}')
        return 1


def main():
    root_dir = Path(__file__).resolve().parent.parent
    checker = ModuleArchitectureChecker(root_dir)
    return checker.run()


if __name__ == "__main__":
    raise SystemExit(main())
