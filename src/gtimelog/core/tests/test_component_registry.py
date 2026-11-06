import unittest

from gtimelog.models import (
    ComponentRegistry,
    Controller,
    Model,
    Service,
    component_registry,
)


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

        with self.assertRaises(ValueError):
            self.reg.register(Bad)

    def test_no_name_no_inherit_raises(self):
        class NoAttrs:
            pass

        with self.assertRaises(ValueError):
            self.reg.register(NoAttrs)

    def test_get_nonexistent_raises(self):
        with self.assertRaises(KeyError):
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
    def test_subclass_with_name_registers_itself(self):
        class Gadget(Model):
            _name = 'test.auto.gadget'

        assert component_registry.get('test.auto.gadget') is Gadget

    def test_environment_returns_class_and_instance(self):
        class Counter(Service):
            _name = 'test.auto.counter'

            def __init__(self, start=0):
                self.start = start

        env = Counter().env
        assert env['test.auto.counter'] is Counter
        assert env.get('test.auto.counter', 5).start == 5

    def test_controller_keeps_its_window(self):
        window = object()
        assert Controller(window).window is window


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
