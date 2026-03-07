"""Compatibility facade for the split core component framework.

The implementation now lives under ``gtimelog.core.components``:
- registry: component registration/merging
- environment: Odoo-style access helper
- component: Component/Model/Service/Controller hierarchy
- hook: declarative hook registration
"""

from gtimelog.core.components import (
    Component,
    ComponentRegistry,
    Controller,
    Environment,
    Hook,
    Model,
    Service,
    component_registry,
)

__all__ = [
    'ComponentRegistry',
    'component_registry',
    'Environment',
    'Component',
    'Model',
    'Service',
    'Controller',
    'Hook',
]
