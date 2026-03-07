"""Application service for managing GTK application operations.

This module provides ApplicationService, a Service component that encapsulates
access to GTK/GObject operations via the lazy-loaded gi() classmethod.

All methods use self.gi() to avoid direct imports of GTK modules while
maintaining compatibility with the gi introspection library.

This is a core application service used by all addons that need GTK operations.
It belongs in the application layer (not addon-specific) because it provides
infrastructure for desktop integration, not addon business logic.
"""

from gtimelog.models import Service


class ApplicationService(Service):
    """Service for managing GTK Application operations.

    Centralizes GTK/GObject module access through the lazy-loaded gi() method,
    avoiding direct imports of gi.repository modules in Controllers and Views.

    All factory methods and utilities delegate to self.gi() for module access,
    which maintains a shared class-level cache of imported modules.

    Usage pattern:
        service = component_registry.get('application.service')()
        action = service.create_simple_action('quit')
        settings = service.create_settings('org.gtimelog.GTimeLog')

    The gi() method provided by the Service base class lazily imports:
        - Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk
        - optionally: Soup (if available)

    These modules are cached at the class level after first import, ensuring
    efficient access across all ApplicationService instances.
    """

    _name = 'application.service'

    def create_simple_action(self, name, parameter_type=None):
        """Create a Gio.SimpleAction for the application.

        Args:
            name: Unique action name (e.g., 'quit', 'preferences').
            parameter_type: Optional GLib.VariantType for the action parameter.
                          Use None for stateless actions, 's' for string, etc.

        Returns:
            Gio.SimpleAction: The created action ready for attachment to application.

        Example:
            action = service.create_simple_action('quit')
            action = service.create_simple_action('open-file', 's')
        """
        return self.gi().Gio.SimpleAction.new(name, parameter_type)

    def create_property_action(self, name, obj, property_name):
        """Create a Gio.PropertyAction bound to an object property.

        Gio.PropertyAction creates an action that controls a property on an object,
        useful for toggling boolean flags or controlling application state.

        Args:
            name: Unique action name.
            obj: GObject instance to bind property to.
            property_name: Name of the property on obj (e.g., 'visible', 'enabled').

        Returns:
            Gio.PropertyAction: The created property action.

        Example:
            action = service.create_property_action('show-log', window, 'visible')
        """
        return self.gi().Gio.PropertyAction.new(name, obj, property_name)

    def create_settings(self, schema_id):
        """Create Gio.Settings for application configuration.

        Loads settings from the system GSettings schema identified by schema_id.
        The schema must be installed in the system (via .gschema.xml files in
        /usr/share/glib-2.0/schemas or development environments).

        Args:
            schema_id: GSettings schema ID string (e.g., 'org.gtimelog.GTimeLog').

        Returns:
            Gio.Settings: Settings object for reading/writing configuration values.

        Raises:
            GLib.Error: If schema_id is not found or unavailable.

        Example:
            settings = service.create_settings('org.gtimelog.GTimeLog')
            window_state = settings.get_string('window-state')
        """
        return self.gi().Gio.Settings.new(schema_id)

    def get_settings_schema_source(self):
        """Get the default Gio.SettingsSchemaSource for schema lookup.

        Returns:
            Gio.SettingsSchemaSource: The default system schema source.

        Usage:
            source = service.get_settings_schema_source()
            schema = source.lookup('org.gtimelog.GTimeLog', False)
        """
        return self.gi().Gio.SettingsSchemaSource.get_default()

    def lookup_schema(self, schema_id):
        """Lookup a schema in the default GSettings schema source.

        Queries the system schema source to check if a schema exists and retrieve
        its metadata without creating a Settings instance.

        Args:
            schema_id: GSettings schema ID to lookup.

        Returns:
            Gio.SettingsSchema: Schema object if found, None if not available.

        Example:
            schema = service.lookup_schema('org.gtimelog.GTimeLog')
            if schema is not None:
                settings = service.create_settings('org.gtimelog.GTimeLog')
        """
        source = self.get_settings_schema_source()
        return source.lookup(schema_id, False)

    def set_application_name(self, name):
        """Set the application display name globally.

        This name is used by the desktop environment and system utilities.
        Should be called early in application startup.

        Args:
            name: Human-readable application name (e.g., 'GTimeLog').

        Example:
            service.set_application_name('GTimeLog')
        """
        self.gi().GLib.set_application_name(name)

    def set_prgname(self, name):
        """Set the program name in the process environment.

        The program name is used in error messages, log output, and process identification.
        Should be called early in application startup.

        Args:
            name: Program identifier (e.g., 'gtimelog').

        Example:
            service.set_prgname('gtimelog')
        """
        self.gi().GLib.set_prgname(name)

    def get_application_flags(self):
        """Get the Gio.ApplicationFlags enumeration.

        Returns:
            Type: Gio.ApplicationFlags enum for checking/setting app behavior flags.

        Usage:
            flags = service.get_application_flags()
            app_flags = flags.HANDLES_OPEN | flags.HANDLES_COMMAND_LINE
        """
        return self.gi().Gio.ApplicationFlags

    def filename_to_uri(self, filename):
        """Convert a filesystem path to a URI string.

        Handles platform-specific path encoding and URI formatting.
        Useful for passing local filenames to methods expecting URIs.

        Args:
            filename: Filesystem path string (absolute or relative).

        Returns:
            str: URI string (e.g., 'file:///home/user/file.txt').

        Raises:
            GLib.Error: If filename cannot be converted to URI.

        Example:
            uri = service.filename_to_uri('/home/user/document.pdf')
        """
        return self.gi().GLib.filename_to_uri(filename, None)

    def show_uri(self, uri):
        """Open a URI in the default application.

        Delegates to the desktop environment to open URLs in web browsers,
        email clients, or other appropriate applications.

        Args:
            uri: URI string (e.g., 'https://example.com', 'mailto:user@example.com').

        Returns:
            bool: True if successful, False otherwise.

        Example:
            service.show_uri('https://gtimelog.org')
            service.show_uri('mailto:support@example.com')
        """
        return self.gi().Gtk.show_uri(None, uri, self.gi().Gdk.CURRENT_TIME)

    def get_monotonic_time(self):
        """Get the current monotonic time in milliseconds.

        Monotonic time is unaffected by system clock adjustments and is useful
        for measuring elapsed time or implementing timeouts that don't jump.

        Returns:
            int: Current monotonic time in milliseconds.

        Note:
            The absolute value is meaningless; use for differences/intervals.

        Example:
            start_ms = service.get_monotonic_time()
            # ... do work ...
            elapsed_ms = service.get_monotonic_time() - start_ms
        """
        return self.gi().GLib.get_monotonic_time() // 1000

    def get_default_screen(self):
        """Get the default display screen.

        Returns:
            Gdk.Screen: The default Gdk.Screen object for the display.

        Usage:
            screen = service.get_default_screen()
            if screen:
                screen.get_width()  # Get screen dimensions
        """
        return self.gi().Gdk.Screen.get_default()

    def idle_add(self, callback, *args):
        """Schedule a callback to run in the GTK main loop at idle priority.

        Idle callbacks are executed when the main loop has processed all
        higher-priority events. Useful for deferring non-urgent work
        without blocking user interaction.

        Args:
            callback: Callable to execute in the main loop.
            *args: Arguments to pass to callback on execution.

        Returns:
            int: Handler ID. Can be used to remove via GLib.source_remove().

        Example:
            handler_id = service.idle_add(self.on_idle)
            handler_id = service.idle_add(self.update_label, 'Loading...')
            # Later: GLib.source_remove(handler_id) to cancel

        Important:
            The callback should return False to run only once, or True to
            reschedule itself.
        """
        return self.gi().GLib.idle_add(callback, *args)

    def bind_settings(self, settings, property_name, widget, widget_property):
        """Bind a GSettings property to a widget property.

        Creates a two-way binding between a GSettings property and a widget's
        property, automatically synchronizing values when either changes.

        Args:
            settings: Gio.Settings object with the property to bind.
            property_name: Name of the settings property (e.g., 'show-log').
            widget: GObject with the property to keep in sync.
            widget_property: Name of the widget property (e.g., 'visible', 'text').

        Returns:
            None

        Example:
            gs = component_registry.get('base.settings')()
            service.bind_settings(gs, 'show-log', window, 'visible')

        Common Widget Properties:
            - Gtk.CheckButton/Switch: 'active'
            - Gtk.Entry/TextView: 'text'
            - Gtk.SpinButton: 'value'
            - Gtk.ComboBoxText: 'active-id'
            - Gtk.Adjustment: 'value'
            - Any GObject: 'visible', 'sensitive', 'tooltip-text'
        """
        flags = self.gi().Gio.SettingsBindFlags.DEFAULT
        settings.bind(property_name, widget, widget_property, flags)

    def create_builder_from_file(self, ui_file_path):
        """Load a GTK UI definition from a .ui file.

        Gtk.Builder loads XML UI definitions (generated by Glade or hand-written)
        into a runtime object tree. Useful for separating UI layout from code.

        Args:
            ui_file_path: Path to .ui file (absolute or relative to working dir).

        Returns:
            Gtk.Builder: Builder object containing loaded widgets accessible
                        via builder.get_object(widget_name).

        Raises:
            GLib.Error: If file not found or XML is malformed.

        Example:
            builder = service.create_builder_from_file('dialog.ui')
            dialog = builder.get_object('dialog')
            dialog.run()

        Best Practices:
            - Store frequently accessed objects: dialog = builder.get_object('dialog')
            - Connect signal handlers: builder.connect_signals(self)
            - Keep .ui files close to controller code
        """
        return self.gi().Gtk.Builder.new_from_file(ui_file_path)

    def create_action_variant(self, format_string, *values):
        """Create a GLib.Variant for passing to action signals.

        GLib.Variant is a type-safe container for transmitting structured data
        through GObject signals and D-Bus messages.

        Args:
            format_string: GVariant format string ('s'=string, 'i'=int, 'b'=bool, etc.).
            *values: values matching the format string.

        Returns:
            GLib.Variant: Typed container with the supplied values.

        Common Format Strings:
            - 's': string (str)
            - 'i': 32-bit integer (int)
            - 'u': 32-bit unsigned (int)
            - 'b': boolean (bool)
            - 'd': double (float)
            - 'o': object path (str)
            - '()': empty variant (no args)

        Example:
            variant = service.create_action_variant('s', 'daily')
            action.activate(variant)

            variant = service.create_action_variant('i', 42)
            other_action.activate(variant)
        """
        return self.gi().GLib.Variant(format_string, *values)

    def get_settings_bind_flags(self):
        """Get Gio.SettingsBindFlags enum for advanced binding control.

        Returns flags for controlling how settings bind to widget properties.

        Returns:
            Type: Gio.SettingsBindFlags enum with options:
                - DEFAULT: basic two-way binding
                - GET: read settings to widget only (one-way)
                - SET: write widget changes to settings only (one-way)
                - NO_CHANGES: don't sync changes
                - GET_NO_CHANGES: disable further reads
                - INVERT_BOOLEAN: invert boolean values during binding

        Usage:
            flags = service.get_settings_bind_flags()
            settings.bind('property', widget, 'prop', flags.GET)
        """
        return self.gi().Gio.SettingsBindFlags

    def timeout_add_seconds(self, seconds, callback, *args):
        """Schedule a callback to run after a delay.

        Unlike idle_add(), timeout_add_seconds() waits for the specified
        interval before first execution. Useful for polling, auto-save timers,
        or periodic updates.

        Args:
            seconds: Delay in seconds before callback execution.
            callback: Callable to execute.
            *args: Arguments to pass to callback.

        Returns:
            int: Handler ID. Can be used to remove via GLib.source_remove().

        Example:
            # Auto-save every 30 seconds
            self.save_timer_id = service.timeout_add_seconds(30, self.auto_save)
            # Later: GLib.source_remove(service.save_timer_id)

        Important:
            Return False from callback to remove timeout, True to reschedule.
        """
        return self.gi().GLib.timeout_add_seconds(seconds, callback, *args)

    def connect_settings_changed(self, settings, signal_name, callback):
        """Connect a callback to a GSettings changed signal.

        Listen for changes to a specific or all settings properties.

        Args:
            settings: Gio.Settings object.
            signal_name: 'changed::property-name' or 'changed' for all changes.
            callback: Function(settings, key) called when property changes.

        Returns:
            int: Handler ID for disconnection via settings.disconnect().

        Example:
            service.connect_settings_changed(gs, 'changed::show-log', self.on_show_log_changed)
            # on_show_log_changed(gs, 'show-log')

            service.connect_settings_changed(gs, 'changed', self.on_any_setting_changed)
            # on_any_setting_changed(gs, 'property-name')
        """
        return settings.connect(signal_name, callback)
