import ast
import importlib
import logging
import os
import sys

log = logging.getLogger('gtimelog.addons')


class AddonRegistry:
    """Central registry for gtimelog addons."""

    NON_TOGGLEABLE_ADDONS = frozenset({'base', 'timelog'})
    ALLOWED_MODULE_TYPES = frozenset({'technical', 'functional'})
    ALLOWED_LAYERS = frozenset({'platform', 'ui', 'feature', 'integration'})
    DEFAULT_MODULE_TYPE = 'functional'
    DEFAULT_LAYER = 'feature'
    DEFAULT_DOMAIN = 'general'

    def __init__(self):
        self._addons = {}  # name -> addon module
        self._manifests = {}  # name -> manifest dict
        self._export_handlers = {}  # name -> callable(window) -> str
        self._hooks = {}  # hook_name -> [callable]
        self._discovered_paths = set()
        self._pending = {}  # name -> (addon_dir, parent_path)
        self._disabled_addons_requested = set()
        self._disabled_addons_effective = set()

    # ------------------------------------------------------------------
    # Discovery & loading
    # ------------------------------------------------------------------

    def discover(self, paths=None, disabled_addons=None):
        """Scan directories for addon packages and load them.

        Addons are loaded in dependency order: if addon B depends on
        addon A, A is loaded first.
        """
        if paths is None:
            paths = self._default_paths()

        for path in paths:
            path = os.path.abspath(path)
            if path in self._discovered_paths:
                continue
            self._discovered_paths.add(path)

            if not os.path.isdir(path):
                continue

            for entry in sorted(os.listdir(path)):
                addon_dir = os.path.join(path, entry)
                if not os.path.isdir(addon_dir):
                    continue
                if not os.path.isfile(os.path.join(addon_dir, '__init__.py')):
                    continue
                if entry.startswith('_'):
                    continue
                if entry not in self._addons and entry not in self._pending:
                    manifest = self._read_manifest(addon_dir)
                    self._manifests[entry] = manifest
                    self._pending[entry] = (addon_dir, path)

        self._disabled_addons_requested = set(disabled_addons or ())
        self._disabled_addons_effective = self.compute_effective_disabled(self._disabled_addons_requested)

        load_order = self._resolve_load_order()
        for name in load_order:
            if name in self._pending:
                if name in self._disabled_addons_effective:
                    continue
                addon_dir, parent_path = self._pending.pop(name)
                self._do_load_addon(name, addon_dir, parent_path)

    def _resolve_load_order(self):
        """Topological sort of pending addons by ``depends``."""
        visited = set()
        order = []

        def visit(name):
            if name in visited:
                return
            visited.add(name)
            manifest = self._manifests.get(name, {})
            for dep in manifest.get('depends', []):
                if dep in self._pending:
                    visit(dep)
            order.append(name)

        for name in sorted(self._pending):
            visit(name)
        return order

    def _default_paths(self):
        gtimelog_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        paths = [os.path.join(gtimelog_root, 'addons')]
        env_paths = os.environ.get('GTIMELOG_ADDONS_PATH', '')
        if env_paths:
            paths.extend(p.strip() for p in env_paths.split(':') if p.strip())
        return paths

    def _do_load_addon(self, name, addon_dir, parent_path):
        if name in self._addons:
            return

        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)

        try:
            module_name = f'gtimelog.addons.{name}'
            mod = importlib.import_module(module_name)
            self._addons[name] = mod
            log.debug('Loaded addon: %s', name)
        except Exception:
            log.exception('Failed to load addon: %s', name)

    @staticmethod
    def _read_manifest(addon_dir):
        manifest_file = os.path.join(addon_dir, '__manifest__.py')
        if not os.path.isfile(manifest_file):
            return {}
        try:
            with open(manifest_file) as f:
                return ast.literal_eval(f.read())
        except Exception:
            log.exception('Failed to read manifest: %s', manifest_file)
            return {}

    # ------------------------------------------------------------------
    # Addon queries
    # ------------------------------------------------------------------

    def get_addon(self, name):
        return self._addons.get(name)

    def list_addons(self):
        return list(self._addons.keys())

    def list_known_addons(self):
        return sorted(self._manifests.keys())

    def list_toggleable_addons(self):
        module_type_order = {'technical': 0, 'functional': 1}
        layer_order = {'platform': 0, 'ui': 1, 'feature': 2, 'integration': 3}
        return sorted(
            (name for name in self.list_known_addons() if name not in self.NON_TOGGLEABLE_ADDONS),
            key=lambda name: (
                module_type_order[self.get_module_type(name)],
                layer_order[self.get_layer(name)],
                name,
            ),
        )

    def get_module_type(self, name):
        value = self.get_manifest(name).get('module_type', self.DEFAULT_MODULE_TYPE)
        if value not in self.ALLOWED_MODULE_TYPES:
            return self.DEFAULT_MODULE_TYPE
        return value

    def get_layer(self, name):
        value = self.get_manifest(name).get('layer', self.DEFAULT_LAYER)
        if value not in self.ALLOWED_LAYERS:
            return self.DEFAULT_LAYER
        return value

    def get_domain(self, name):
        return self.get_manifest(name).get('domain', self.DEFAULT_DOMAIN)

    def get_module_metadata(self, name):
        return {
            'module_type': self.get_module_type(name),
            'layer': self.get_layer(name),
            'domain': self.get_domain(name),
        }

    def list_addons_by_module_type(self, module_type, only_toggleable=False):
        names = self.list_known_addons()
        if only_toggleable:
            names = [name for name in names if name not in self.NON_TOGGLEABLE_ADDONS]
        return sorted(name for name in names if self.get_module_type(name) == module_type)

    def get_disabled_addons_effective(self):
        return sorted(self._disabled_addons_effective)

    def compute_effective_disabled(self, disabled_addons):
        requested = {
            name for name in disabled_addons if name in self._manifests and name not in self.NON_TOGGLEABLE_ADDONS
        }
        enabled = set(self._manifests.keys()) - requested

        changed = True
        while changed:
            changed = False
            for addon in tuple(enabled):
                for dep in self.get_dependency_closure(addon):
                    if dep in requested:
                        requested.remove(dep)
                        enabled.add(dep)
                        changed = True

        return requested

    def get_dependency_closure(self, addon):
        closure = set()
        stack = list(self.get_manifest(addon).get('depends', []))
        while stack:
            dep = stack.pop()
            if dep in closure:
                continue
            closure.add(dep)
            stack.extend(self.get_manifest(dep).get('depends', []))
        return closure

    def get_required_by_enabled(self, addon, disabled_addons):
        effective_disabled = self.compute_effective_disabled(disabled_addons)
        enabled = set(self.list_known_addons()) - effective_disabled
        required_by = []
        for candidate in sorted(enabled):
            if addon in self.get_dependency_closure(candidate):
                required_by.append(candidate)
        return required_by

    def get_manifest(self, name):
        return self._manifests.get(name, {})

    # ------------------------------------------------------------------
    # Export handler registration (used by export addons)
    # ------------------------------------------------------------------

    def register_export_handler(self, name, handler):
        """Register an export handler callable.

        *handler* receives a ``TimeWindow`` and returns a string (e.g. CSV).
        """
        self._export_handlers[name] = handler
        log.debug('Registered export handler: %s', name)

    def get_export_handler(self, name):
        return self._export_handlers.get(name)

    # ------------------------------------------------------------------
    # Hook system (observer pattern for cross-addon communication)
    # ------------------------------------------------------------------

    def register_hook(self, hook_name, callback):
        """Register a callback for a named hook point."""
        self._hooks.setdefault(hook_name, []).append(callback)

    def trigger_hook(self, hook_name, *args, **kwargs):
        """Call all callbacks registered for *hook_name*."""
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                results.append(callback(*args, **kwargs))
            except Exception:
                log.exception('Hook %s callback %s failed', hook_name, callback)
        return results

    # ------------------------------------------------------------------
    # Reset (for testing)
    # ------------------------------------------------------------------

    def reset(self):
        self._addons.clear()
        self._manifests.clear()
        self._export_handlers.clear()
        self._hooks.clear()
        self._discovered_paths.clear()
        self._pending.clear()
        self._disabled_addons_requested.clear()
        self._disabled_addons_effective.clear()
