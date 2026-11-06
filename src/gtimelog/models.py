"""Public names of the component framework, implemented in ``gtimelog.core.components``:

- registry: component registration/merging
- environment: Odoo-style access helper
- component: Component/Model/Service/Controller hierarchy
"""

from gtimelog.core.components import (
    AbstractModel,
    Component,
    ComponentRegistry,
    Controller,
    Environment,
    Model,
    Service,
    component_registry,
)


__all__ = [
    'AbstractModel',
    'Component',
    'ComponentRegistry',
    'Controller',
    'Environment',
    'Model',
    'Service',
    'component_registry',
]
