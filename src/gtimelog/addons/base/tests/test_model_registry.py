import unittest

import pytest

from gtimelog.core.registry.addons import AddonRegistry
from gtimelog.models import ComponentRegistry, Controller, Hook, Model, Service


class TestComponentRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = ComponentRegistry()

    def test_register_base_model(self):
        class MyModel:
            _name = 'my.model'

            def hello(self):
                return 'hello'

        self.reg.register(MyModel)
        assert self.reg.is_registered('my.model')
        cls = self.reg.get('my.model')
        assert cls is MyModel
        assert cls().hello() == 'hello'

    def test_register_and_inherit(self):
        class Base:
            _name = 'base.model'

            def value(self):
                return 1

        class Extension:
            _inherit = 'base.model'

            def extra(self):
                return 2

        self.reg.register(Base)
        self.reg.register(Extension)

        Merged = self.reg.get('base.model')
        obj = Merged()
        assert obj.value() == 1
        assert obj.extra() == 2

    def test_inherit_overrides_method(self):
        class Base:
            _name = 'overridable'

            def compute(self):
                return 'base'

        class Override:
            _inherit = 'overridable'

            def compute(self):
                return 'overridden'

        self.reg.register(Base)
        self.reg.register(Override)

        Merged = self.reg.get('overridable')
        assert Merged().compute() == 'overridden'

    def test_super_call_in_override(self):
        class Base:
            _name = 'chainable'

            def items(self):
                return ['base']

        class Ext:
            _inherit = 'chainable'

            def items(self):
                return [*super().items(), 'ext']

        self.reg.register(Base)
        self.reg.register(Ext)

        Merged = self.reg.get('chainable')
        assert Merged().items() == ['base', 'ext']

    def test_multiple_extensions(self):
        class Base:
            _name = 'multi'

            def parts(self):
                return ['base']

        class Ext1:
            _inherit = 'multi'

            def parts(self):
                return [*super().parts(), 'ext1']

        class Ext2:
            _inherit = 'multi'

            def parts(self):
                return [*super().parts(), 'ext2']

        self.reg.register(Base)
        self.reg.register(Ext1)
        self.reg.register(Ext2)

        Merged = self.reg.get('multi')
        assert Merged().parts() == ['base', 'ext1', 'ext2']

    def test_inherit_nonexistent_raises(self):
        class Bad:
            _inherit = 'nonexistent'

        with pytest.raises(ValueError):
            self.reg.register(Bad)

    def test_no_name_no_inherit_raises(self):
        class NoAttrs:
            pass

        with pytest.raises(ValueError):
            self.reg.register(NoAttrs)

    def test_get_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.reg.get('nope')

    def test_list_components(self):
        class A:
            _name = 'a'

        class B:
            _name = 'b'

        self.reg.register(A)
        self.reg.register(B)
        assert sorted(self.reg.list()) == ['a', 'b']

    def test_decorator_usage(self):
        @self.reg.register
        class Decorated:
            _name = 'decorated'

        assert self.reg.get('decorated') is Decorated

    def test_reset(self):
        class M:
            _name = 'temp'

        self.reg.register(M)
        assert self.reg.is_registered('temp')
        self.reg.reset()
        assert not self.reg.is_registered('temp')

    def test_cache_invalidation_on_new_extension(self):
        class Base:
            _name = 'cached'

            def val(self):
                return 1

        self.reg.register(Base)
        First = self.reg.get('cached')
        assert First().val() == 1

        class Ext:
            _inherit = 'cached'

            def val(self):
                return 2

        self.reg.register(Ext)
        Second = self.reg.get('cached')
        assert Second().val() == 2
        assert First is not Second

    def test_delegation_new_name_inheriting_another(self):
        class Base:
            _name = 'parent'

            def who(self):
                return 'parent'

        class Child:
            _name = 'child'
            _inherit = 'parent'

            def who(self):
                return 'child'

        self.reg.register(Base)
        self.reg.register(Child)

        assert self.reg.is_registered('child')
        assert self.reg.is_registered('parent')
        ChildCls = self.reg.get('child')
        assert ChildCls().who() == 'child'

    def test_list_by_kind(self):
        """Test filtering components by type (Model, Service, Controller)."""

        class MyModel(Model):
            _name = 'test.model'

        class MySvc(Service):
            _name = 'test.service'

        class MyCtrl(Controller):
            _name = 'test.controller'

        # Auto-registered by metaclass, but we use a fresh registry
        self.reg.register(MyModel)
        self.reg.register(MySvc)
        self.reg.register(MyCtrl)

        assert self.reg.list(Model) == ['test.model']
        assert self.reg.list(Service) == ['test.service']
        assert self.reg.list(Controller) == ['test.controller']
        assert sorted(self.reg.list()) == ['test.controller', 'test.model', 'test.service']

    def test_service_as_namespace(self):
        """Test that Service subclass works as a namespace."""

        class MathService(Service):
            _name = 'math'
            PI = 3.14

            @staticmethod
            def add(a, b):
                return a + b

        self.reg.register(MathService)
        svc = self.reg.get('math')
        assert svc.PI == 3.14
        assert svc.add(2, 3) == 5


class TestComponentAutoRegistration(unittest.TestCase):
    """Test that Component subclasses auto-register via metaclass."""

    def test_model_auto_registers(self):
        from gtimelog import component_registry
        from gtimelog.addons import registry

        registry.discover()

        assert component_registry.is_registered('entry')
        assert component_registry.is_registered('time.log')
        assert component_registry.is_registered('settings')
        assert component_registry.is_registered('task.list')
        assert component_registry.is_registered('report.record')

    def test_service_auto_registers(self):
        from gtimelog import component_registry
        from gtimelog.addons import registry

        registry.discover()

        assert component_registry.is_registered('office_hours')
        assert component_registry.is_registered('mail_sender')
        assert component_registry.is_registered('report.mail.delivery')
        assert component_registry.is_registered('reports.service')

    def test_controller_auto_registers(self):
        from gtimelog import component_registry
        from gtimelog.addons import registry

        registry.discover()

        assert component_registry.is_registered('exports')
        assert component_registry.is_registered('reports')

    def test_get_returns_correct_class(self):
        from gtimelog import component_registry
        from gtimelog.addons.base.models import Entry, Settings
        from gtimelog.addons.timelog.models import TimeLog

        assert component_registry.get('entry') is Entry
        assert component_registry.get('time.log') is TimeLog
        # Settings is extended by multiple addons, so we get a merged class
        # Check that it's a subclass of the base Settings
        merged_settings = component_registry.get('settings')
        assert issubclass(merged_settings, Settings)

    def test_service_provides_api(self):
        from gtimelog import component_registry
        from gtimelog.addons import registry

        registry.discover()

        office = component_registry.get('office_hours')
        assert hasattr(office, 'time_left_at_work')
        assert hasattr(office, 'estimated_week_overtime')
        assert hasattr(office, 'office_time_status')

        mail = component_registry.get('mail_sender')
        assert hasattr(mail, 'EmailError')
        assert hasattr(mail, 'MAIL_PROTOCOLS')
        assert hasattr(mail, 'prepare_message')

        report_delivery = component_registry.get('report.mail.delivery')
        assert hasattr(report_delivery, 'send_report')
        assert getattr(report_delivery, 'OVERRIDE_SOURCE', None) == 'mail_sender-addon-integration'

        reports_app = component_registry.get('application.reports.service')
        assert getattr(reports_app, 'OVERRIDE_SOURCE', None) == 'reports-addon-application'

        reports_domain = component_registry.get('domain.reports.service')
        assert getattr(reports_domain, 'OVERRIDE_SOURCE', None) == 'reports-addon-domain'

        entry_parser = component_registry.get('platform.entry.parser')
        assert getattr(entry_parser, 'OVERRIDE_SOURCE', None) == 'reports-addon-platform'

        tasks_domain = component_registry.get('domain.tasks.policy')
        assert getattr(tasks_domain, 'OVERRIDE_SOURCE', None) == 'tasks-addon-domain'

        tasks_app = component_registry.get('application.tasks.service')
        assert getattr(tasks_app, 'OVERRIDE_SOURCE', None) == 'tasks-addon-application'

        rpt_svc = component_registry.get('reports.service')
        assert hasattr(rpt_svc, 'REPORT_KINDS')
        assert hasattr(rpt_svc, 'Reports')
        assert hasattr(rpt_svc, 'ReportRecord')


class TestAddonRegistryActivation(unittest.TestCase):
    def setUp(self):
        self.registry = AddonRegistry()
        self.registry._manifests = {
            'base': {'depends': []},
            'timelog': {'depends': ['base']},
            'tasks': {'depends': ['base']},
            'reports': {'depends': ['tasks']},
            'reports_csv': {'depends': ['reports']},
        }

    def test_non_toggleable_addons_stay_enabled(self):
        disabled = self.registry.compute_effective_disabled({'base', 'timelog'})
        assert 'base' not in disabled
        assert 'timelog' not in disabled

    def test_required_dependency_is_auto_enabled(self):
        disabled = self.registry.compute_effective_disabled({'tasks'})
        assert 'tasks' not in disabled

    def test_disable_leaf_addon_is_kept(self):
        disabled = self.registry.compute_effective_disabled({'reports_csv'})
        assert 'reports_csv' in disabled

    def test_required_by_enabled_reports_transitive(self):
        required_by = self.registry.get_required_by_enabled('tasks', {'tasks'})
        assert 'reports' in required_by
        assert 'reports_csv' in required_by

    def test_discover_skips_effectively_disabled(self):
        load_order = []
        self.registry._pending = {
            'base': ('/tmp/base', '/tmp'),
            'timelog': ('/tmp/timelog', '/tmp'),
            'tasks': ('/tmp/tasks', '/tmp'),
            'reports': ('/tmp/reports', '/tmp'),
            'reports_csv': ('/tmp/reports_csv', '/tmp'),
        }

        def _fake_load(name, addon_dir, parent_path):
            del addon_dir, parent_path
            load_order.append(name)

        self.registry._do_load_addon = _fake_load
        self.registry._discovered_paths.add('/tmp')

        self.registry.discover(paths=[], disabled_addons=['reports_csv'])
        assert 'reports_csv' not in load_order
        assert 'reports' in load_order


class TestAddonRegistryMetadata(unittest.TestCase):
    def setUp(self):
        self.registry = AddonRegistry()
        self.registry._manifests = {
            'base': {
                'depends': [],
                'module_type': 'technical',
                'layer': 'platform',
                'domain': 'core',
            },
            'timelog': {
                'depends': ['base'],
                'module_type': 'functional',
                'layer': 'feature',
                'domain': 'timelog',
            },
            'weird': {
                'depends': ['base'],
                'module_type': 'invalid',
                'layer': 'invalid',
            },
        }

    def test_get_module_metadata_uses_defaults_for_invalid_values(self):
        assert self.registry.get_module_type('weird') == AddonRegistry.DEFAULT_MODULE_TYPE
        assert self.registry.get_layer('weird') == AddonRegistry.DEFAULT_LAYER
        assert self.registry.get_domain('weird') == AddonRegistry.DEFAULT_DOMAIN

    def test_get_module_metadata_returns_expected_dict(self):
        assert self.registry.get_module_metadata('timelog') == {
            'module_type': 'functional',
            'layer': 'feature',
            'domain': 'timelog',
        }

    def test_list_addons_by_module_type(self):
        assert set(self.registry.list_addons_by_module_type('technical')) == {'base'}
        assert set(self.registry.list_addons_by_module_type('functional')) == {'timelog', 'weird'}

    def test_list_addons_by_module_type_toggleable(self):
        assert self.registry.list_addons_by_module_type('technical', only_toggleable=True) == []
        assert self.registry.list_addons_by_module_type('functional', only_toggleable=True) == ['weird']

    def test_list_toggleable_addons_sorted_by_type_layer_name(self):
        assert self.registry.list_toggleable_addons() == ['weird']


class TestHookAutoRegistration(unittest.TestCase):
    """Test that Hook subclasses auto-register methods via metaclass."""

    def setUp(self):
        from gtimelog.addons import registry

        self._original_hooks = dict(registry._hooks)
        registry._hooks = {}

    def tearDown(self):
        from gtimelog.addons import registry

        registry._hooks = self._original_hooks

    def test_simple_hook_registration(self):
        from gtimelog.addons import registry

        calls = []

        class MyHooks(Hook):
            def window_init(window):
                calls.append(('window_init', window))

        assert 'window_init' in registry._hooks
        assert len(registry._hooks['window_init']) == 1
        registry.trigger_hook('window_init', 'fake_window')
        assert calls == [('window_init', 'fake_window')]

    def test_multiple_hooks_same_class(self):
        from gtimelog.addons import registry

        calls = []

        class MultiHooks(Hook):
            def window_init(window):
                calls.append('window_init')

            def prefs_init(dialog):
                calls.append('prefs_init')

            def app_startup(app):
                calls.append('app_startup')

        assert 'window_init' in registry._hooks
        assert 'prefs_init' in registry._hooks
        assert 'app_startup' in registry._hooks
        registry.trigger_hook('window_init', None)
        registry.trigger_hook('prefs_init', None)
        registry.trigger_hook('app_startup', None)
        assert calls == ['window_init', 'prefs_init', 'app_startup']

    def test_double_underscore_convention(self):
        from gtimelog.addons import registry

        calls = []

        class DunderHooks(Hook):
            def window_init__setup(window):
                calls.append('setup')

            def window_init__settings(window):
                calls.append('settings')

        hooks = registry._hooks.get('window_init', [])
        assert len(hooks) == 2
        registry.trigger_hook('window_init', None)
        assert calls == ['setup', 'settings']

    def test_private_methods_ignored(self):
        from gtimelog.addons import registry

        class PrivateHooks(Hook):
            def _helper():
                pass

            def window_init(window):
                pass

        assert 'window_init' in registry._hooks
        assert '_helper' not in registry._hooks

    def test_non_callable_attributes_ignored(self):
        from gtimelog.addons import registry

        class AttrHooks(Hook):
            some_data = 42

            def prefs_init(dialog):
                pass

        assert 'prefs_init' in registry._hooks
        assert 'some_data' not in registry._hooks

    def test_hooks_are_plain_functions_no_self(self):
        from gtimelog.addons import registry

        results = []

        class NoSelfHooks(Hook):
            def settings_migration(gsettings, old_settings):
                results.append((gsettings, old_settings))

        registry.trigger_hook('settings_migration', 'gs', 'old')
        assert results == [('gs', 'old')]

    def test_empty_hook_class_registers_nothing(self):
        from gtimelog.addons import registry

        class EmptyHooks(Hook):
            pass

        assert registry._hooks == {}

    def test_hook_auto_registers_on_addon_discover(self):
        """Test that initialization hooks have been migrated to Controllers.

        The old hook system used window_init, prefs_init, app_startup hooks.
        These have been transformed to Controllers for better code organization.
        This test verifies that Controllers are registered via component_registry.
        """
        from gtimelog.models import component_registry

        # Controllers should be registered (base classes exist)
        assert component_registry.is_registered('window.controller'), 'WindowController should be registered'
        assert component_registry.is_registered('prefs.controller'), 'PreferencesController should be registered'
        assert component_registry.is_registered('app.controller'), 'ApplicationController should be registered'
        assert component_registry.is_registered('gsettings.migrator'), 'GSettingsMigrator should be registered'


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
