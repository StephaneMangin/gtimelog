"""GTK Centralization Patterns and Refactoring Guide.

This document outlines the refactoring approach for eliminating repeated GTK imports
and method calls across the GTimeLog codebase through a layered architecture.

ARCHITECTURAL LAYERS
====================

1. CORE SERVICES LAYER (gtimelog.core.services)
  Location: src/gtimelog/core/services/
   Purpose: Infrastructure services used across the entire project
   Examples:
     - gtk.py: ApplicationService for GTK operations (desktop integration)
     - export_csv.py: CSV export service
     - export_ical.py: iCalendar export service

   These services are NOT addon-specific. They provide reusable infrastructure
   that multiple addons may depend on.

2. ADDON APPLICATION LAYER (addons.XXX.application)
   Location: src/gtimelog/addons/XXX/application/
   Purpose: Bridge between core services and addon-specific controllers/views
   Pattern: Re-export core services + define addon-integration points
   Example: addons/base/application/__init__.py re-exports ApplicationService

   This layering ensures:
   - Core remains agnostic to addon structure
   - Clear dependency boundaries
   - Easy to trace addon dependencies on core services
   - Supports addon-specific variations if needed

3. ADDON CONTROLLERS & VIEWS (addons.XXX.controllers/views)
   Access core services through the addon application layer:
     from gtimelog.addons.base.application import ApplicationService
     service = ApplicationService()

CORE PRINCIPLE
==============
All Components (Controllers, Services) access GTK modules through the lazy-loaded
classmethod gi() defined in the Component base class (models.py). This avoids
direct 'from gi.repository import X' statements while maintaining performance
through class-level caching.

PATTERN EXPLANATION
===================

1. LAZY-LOADED MODULE ACCESS
   Location: Component.gi() classmethod in models.py
   Pattern: self.gi().Gtk.Widget, self.gi().Gio.Settings, etc.
   Cache: Class-level _gi_modules_cache dictionary
   Benefit: Imports happen once, cached for all instances

   Example:
       builder = self.gi().Gtk.Builder.new_from_file('window.ui')
       settings = self.gi().Gio.Settings.new('org.gtimelog.GTimeLog')

2. SERVICE COMPOSITION FOR GTK OPERATIONS
  Location: gtimelog/core/services/gtk.py (ApplicationService)
   Pattern: Encapsulate GTK factory methods and utilities in Service components
   Access: from gtimelog.addons.base.application import ApplicationService
           app_service = ApplicationService()

   Benefit: Reusable methods, self-documenting code, centralized logic

   Methods provided:
       - create_simple_action(name, parameter_type)
       - create_property_action(name, obj, property_name)
       - create_settings(schema_id)
       - bind_settings(settings, property_name, widget, widget_property)
       - create_builder_from_file(ui_file_path)
       - create_action_variant(format_string, *values)
       - idle_add(callback, *args)
       - timeout_add_seconds(seconds, callback, *args)
       - connect_settings_changed(settings, signal_name, callback)

3. DIRECT IMPORTS (INTENTIONAL EXCEPTIONS)
   Location: Views (Gtk.Widget subclasses), Models (non-Component)
   Reason: Must inherit from GTK classes; direct imports required
   Pattern: Keep 'from gi.repository import Gtk, Gdk, ...' at module level

   Examples:
       - Views extending Gtk.Dialog, Gtk.TreeView, Gtk.Entry
       - Models inheriting from GObject.Object (Authenticator, Settings)
       - Helpers not derived from Component base class

REFACTORING CHECKLIST
====================

For Controllers using repeated GTK patterns:

✓ Import service via addon application layer (addons/base/application)
✓ Replace 'from gi.repository import ...' with self.gi()
✓ For gs.bind(...) patterns, use app_service.bind_settings()
✓ For Gtk.Builder.new_from_file(), use app_service.create_builder_from_file()
✓ For GLib.Variant(), use app_service.create_action_variant()
✓ For Gio.SimpleAction, use app_service.create_simple_action()
✓ Group related GTK operations into dedicated methods

PATTERNS TO REFACTOR
====================

1. SETTINGS BINDING (Most Common)
   Current (Repeated across 5+ Controllers):
       gs = component_registry.get('base.settings')()
       gs.bind('property', widget, 'widget-property', self.gi().Gio.SettingsBindFlags.DEFAULT)

   Refactored:
       from gtimelog.addons.base.application import ApplicationService
       app_service = ApplicationService()
       app_service.bind_settings(gs, 'property', widget, 'widget-property')

   Files affected:
       - addons/office_hours/controllers/window_controller.py (3 bindings) ✓
       - addons/office_hours/controllers/preferences_controller.py (2 bindings) ✓
       - addons/reports/controllers/window_controller.py (5 bindings)
       - addons/reports/controllers/preferences_controller.py (4 bindings)
       - addons/slack_distribution/controllers/window_controller.py (1 binding)

2. UI FILE LOADING
   Current:
       builder = self.gi().Gtk.Builder.new_from_file(UI_FILE_PATH)

   Refactored:
       from gtimelog.addons.base.application import ApplicationService
       app_service = ApplicationService()
       builder = app_service.create_builder_from_file(UI_FILE_PATH)

   Files affected:
       - addons/about/controllers/application_controller.py (1 usage) ✓

3. ACTION VARIANT CREATION
   Current:
       time_range_action.activate(self.gi().GLib.Variant('s', 'value'))

   Refactored:
       app_service = ApplicationService()
       variant = app_service.create_action_variant('s', 'value')
       time_range_action.activate(variant)

   Files affected:
       - addons/reports/controllers/window_controller.py (1 usage)

IMPLEMENTATION ROADMAP
=====================

Phase 1: BASELINE (✓ COMPLETED)
  - Created Component.gi() classmethod with lazy-loading cache
  - Refactored 20 Controllers to use self.gi()
  - Created ApplicationService with 16 methods
  - Created comprehensive test suite (28 tests, all passing)

Phase 2: ARCHITECTURAL LAYERING (✓ COMPLETED)
  - Moved ApplicationService to core layer (gtimelog/core/services/gtk.py)
  - Created addons/base/application/ bridge layer
  - Updated imports (controllers + base models __init__)
  - Verified all 206 tests pass
  - Verified pre-commit passes (all quality gates green)

Phase 3: EXTEND REMAINING CONTROLLERS (IN PROGRESS)
  - office_hours controllers: bind_settings() pattern ✓
  - reports controllers: bind_settings() + create_action_variant()
  - slack_distribution controller: bind_settings()
  - Verify each addon after refactoring

Phase 4: DOCUMENTATION & PATTERNS (IN PROGRESS)
  - Update this guide with layering architecture
  - Create examples for common use-cases
  - Document bridge layer purpose and pattern

TESTING STRATEGY
===============

1. Unit Tests
   - ApplicationService methods (mocked gi()): 28 tests ✓
   - Pattern compliance (gi() usage, no direct imports)

2. Integration Tests
   - Settings binding works end-to-end
   - Builder UI file loading in real GTK context
   - Action variant activation in signals

3. Quality Gates
   - No direct 'from gi.repository' in Controllers: ✓
   - Complexity checks for ApplicationService methods: ✓
   - Architecture validation (no circular dependencies): ✓
   - Pre-commit all gates passing: ✓

PERFORMANCE CONSIDERATIONS
=========================

✓ Lazy Loading: gi() imports only once per Component class
✓ Class-level Cache: _gi_modules_cache shared across all instances
✓ No Import Overhead: Module access is attribute lookup, not import statement
✓ Memory Efficient: Single set of GTK module references per class
✓ Service Instantiation: ApplicationService() is lightweight (no GTK init)

Benchmark: 206 tests execute in ~0.5 seconds with no performance degradation.

ARCHITECTURAL BENEFITS
======================

1. Clear Separation: Core (application/) vs Addon-specific (addons/XXX/)
2. Testability: Easy to mock self.gi() for unit tests
3. Maintainability: Single point of change for GTK patterns
4. Clarity: No import noise in Controller implementations
5. Consistency: Uniform access pattern across 20+ files
6. Extensibility: Easy to add new GTK wrappers to ApplicationService
7. Dependency clarity: Easy to see which addons depend on core services
8. Bridge pattern: Insulates core changes from addon implementations

DIRECTORY STRUCTURE
===================

src/gtimelog/
├── models.py                    # Base Component with gi() classmethod
├── application/
│   ├── __init__.py
│   ├── gtk.py                   # ApplicationService (core GTK infrastructure)
│   ├── export_csv.py            # CSV export service
│   ├── export_ical.py           # iCalendar service
│   ├── timelog.py               # Timelog service
│   └── tasks.py                 # Tasks service
└── addons/
    └── base/
        ├── __init__.py
        ├── models/
        │   ├── __init__.py      # Imports ApplicationService from core
        │   ├── entry.py
        │   ├── settings.py
        │   └── ...
        ├── application/         # Bridge layer for base addon
        │   ├── __init__.py      # Re-exports ApplicationService from core
        │   └── ...
        ├── controllers/
        │   ├── window_controller.py      # Uses ApplicationService via bridge
        │   ├── preferences_controller.py # Uses ApplicationService via bridge
        │   └── ...
        └── views/
            └── ...

MIGRATION EXAMPLES
==================

Example 1: Bind Settings (office_hours/controllers/window_controller.py)
---

BEFORE:
    gs = window.gsettings
    lv = window.log_view
    gs.bind('hours', lv, 'hours', self.gi().Gio.SettingsBindFlags.DEFAULT)
    gs.bind('office-hours', lv, 'office-hours', self.gi().Gio.SettingsBindFlags.DEFAULT)

AFTER:
    from gtimelog.addons.base.application import ApplicationService

    gs = window.gsettings
    lv = window.log_view
    app_service = ApplicationService()
    app_service.bind_settings(gs, 'hours', lv, 'hours')
    app_service.bind_settings(gs, 'office-hours', lv, 'office-hours')

Benefits:
  - No need to know about Gio.SettingsBindFlags
  - Centralized GTK enum access
  - More readable intent (what binding is being done)
  - Easier to add flags variations through method parameters

Example 2: Load UI File (about/controllers/application_controller.py)
---

BEFORE:
    builder = self.gi().Gtk.Builder.new_from_file(ABOUT_DIALOG_UI_FILE)

AFTER:
    from gtimelog.addons.base.application import ApplicationService

    app_service = ApplicationService()
    builder = app_service.create_builder_from_file(ABOUT_DIALOG_UI_FILE)

Benefits:
  - Cleaner separation: GTK operation vs control flow
  - Easier to test (mock the service method)
  - Single method to change for Builder variations

NEXT STEPS
==========

1. Refactor remaining controllers (reports, slack_distribution)
2. Verify all 206 tests pass after each addon refactoring
3. Run pre-commit to ensure all quality gates pass
4. Consider extracting other GTK patterns (e.g., Dialog/Window creation)
5. Document addon-integration points for future addons
"""
