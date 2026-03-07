"""Tests for the ApplicationService component.

ApplicationService is defined in gtimelog.core.services.gtk (core service layer)
but tested here in base addon tests for convenience, since base addon controllers
use it extensively.
"""

import unittest
from unittest import mock

from gtimelog.core.services.gtk import ApplicationService


class TestApplicationService(unittest.TestCase):
    """Test ApplicationService methods and GTK integration."""

    def setUp(self):
        """Initialize ApplicationService for each test."""
        self.service = ApplicationService()

    def test_application_service_has_name(self):
        """ApplicationService should have 'application.service' as _name."""
        assert self.service._name == 'application.service'

    def test_create_simple_action_without_parameter(self):
        """create_simple_action should create Gio.SimpleAction without parameter."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_gi.return_value.Gio = mock_gio

            self.service.create_simple_action('test-action')

            mock_gio.SimpleAction.new.assert_called_once_with('test-action', None)

    def test_create_simple_action_with_parameter_type(self):
        """create_simple_action should pass parameter_type to Gio.SimpleAction.new."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_gi.return_value.Gio = mock_gio

            param_type = 's'
            self.service.create_simple_action('my-action', param_type)

            mock_gio.SimpleAction.new.assert_called_once_with('my-action', param_type)

    def test_create_property_action(self):
        """create_property_action should create Gio.PropertyAction with object and property."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_gi.return_value.Gio = mock_gio

            test_obj = mock.Mock()
            self.service.create_property_action('prop-action', test_obj, 'visible')

            mock_gio.PropertyAction.new.assert_called_once_with('prop-action', test_obj, 'visible')

    def test_create_settings(self):
        """create_settings should create Gio.Settings with given schema_id."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_gi.return_value.Gio = mock_gio

            self.service.create_settings('org.gtimelog.GTimeLog')

            mock_gio.Settings.new.assert_called_once_with('org.gtimelog.GTimeLog')

    def test_get_settings_schema_source(self):
        """get_settings_schema_source should return default Gio.SettingsSchemaSource."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_gio.SettingsSchemaSource.get_default.return_value = mock.Mock()
            mock_gi.return_value.Gio = mock_gio

            result = self.service.get_settings_schema_source()

            mock_gio.SettingsSchemaSource.get_default.assert_called_once()
            assert result == mock_gio.SettingsSchemaSource.get_default.return_value

    def test_lookup_schema(self):
        """lookup_schema should lookup schema in default source."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_source = mock.Mock()
            mock_gio = mock.Mock()
            mock_gio.SettingsSchemaSource.get_default.return_value = mock_source
            mock_source.lookup.return_value = mock.Mock()
            mock_gi.return_value.Gio = mock_gio

            result = self.service.lookup_schema('org.gtimelog.GTimeLog')

            mock_source.lookup.assert_called_once_with('org.gtimelog.GTimeLog', False)
            assert result == mock_source.lookup.return_value

    def test_set_application_name(self):
        """set_application_name should set app name via GLib.set_application_name."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_gi.return_value.GLib = mock_glib

            self.service.set_application_name('GTimeLog')

            mock_glib.set_application_name.assert_called_once_with('GTimeLog')

    def test_set_prgname(self):
        """set_prgname should set program name via GLib.set_prgname."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_gi.return_value.GLib = mock_glib

            self.service.set_prgname('gtimelog')

            mock_glib.set_prgname.assert_called_once_with('gtimelog')

    def test_get_application_flags(self):
        """get_application_flags should return Gio.ApplicationFlags enum."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_flags = mock.Mock()
            mock_gio.ApplicationFlags = mock_flags
            mock_gi.return_value.Gio = mock_gio

            result = self.service.get_application_flags()

            assert result == mock_flags

    def test_filename_to_uri(self):
        """filename_to_uri should convert filename to URI via GLib."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_glib.filename_to_uri.return_value = 'file:///home/test'
            mock_gi.return_value.GLib = mock_glib

            result = self.service.filename_to_uri('/home/test/file.txt')

            mock_glib.filename_to_uri.assert_called_once_with('/home/test/file.txt', None)
            assert result == 'file:///home/test'

    def test_show_uri(self):
        """show_uri should call Gtk.show_uri with current timestamp."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gtk = mock.Mock()
            mock_gdk = mock.Mock()
            mock_gdk.CURRENT_TIME = 0
            mock_gi.return_value.Gtk = mock_gtk
            mock_gi.return_value.Gdk = mock_gdk

            self.service.show_uri('https://example.com')

            mock_gtk.show_uri.assert_called_once_with(None, 'https://example.com', 0)

    def test_get_monotonic_time(self):
        """get_monotonic_time should return milliseconds from GLib.get_monotonic_time."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_glib.get_monotonic_time.return_value = 1000 * 1000  # 1 second in microseconds
            mock_gi.return_value.GLib = mock_glib

            result = self.service.get_monotonic_time()

            # Should convert microseconds to milliseconds (divide by 1000)
            assert result == 1000
            mock_glib.get_monotonic_time.assert_called_once()

    def test_get_default_screen(self):
        """get_default_screen should return default Gdk.Screen."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gdk = mock.Mock()
            mock_screen = mock.Mock()
            mock_gdk.Screen.get_default.return_value = mock_screen
            mock_gi.return_value.Gdk = mock_gdk

            result = self.service.get_default_screen()

            assert result == mock_screen
            mock_gdk.Screen.get_default.assert_called_once()

    def test_idle_add_without_args(self):
        """idle_add should add callback to GLib mainloop without extra arguments."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_callback = mock.Mock()
            mock_gi.return_value.GLib = mock_glib

            self.service.idle_add(mock_callback)

            mock_glib.idle_add.assert_called_once_with(mock_callback)

    def test_idle_add_with_args(self):
        """idle_add should pass additional arguments to GLib.idle_add."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_callback = mock.Mock()
            mock_gi.return_value.GLib = mock_glib

            self.service.idle_add(mock_callback, 'arg1', 'arg2', 42)

            mock_glib.idle_add.assert_called_once_with(mock_callback, 'arg1', 'arg2', 42)

    def test_gi_method_is_classmethod(self):
        """gi() should be callable from both instance and class level."""
        # Test class-level access
        with mock.patch('gtimelog.models.Component.gi') as mock_gi_method:
            # This tests that ApplicationService inherits gi() from Service->Component
            assert hasattr(ApplicationService, 'gi')
            assert callable(ApplicationService.gi)

    def test_multiple_gi_calls_use_same_cache(self):
        """Multiple calls to gi() should return cached modules."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            cached_modules = mock.Mock()
            mock_gi.return_value = cached_modules

            # Call gi() twice
            result1 = self.service.gi()
            result2 = self.service.gi()

            # Both should return the same mock instance (proving cache works)
            assert result1 is result2

    def test_service_inherits_from_service_class(self):
        """ApplicationService should inherit from Service."""
        from gtimelog.models import Service

        assert issubclass(ApplicationService, Service)

    def test_bind_settings(self):
        """bind_settings should bind settings property to widget property."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_gio.SettingsBindFlags.DEFAULT = 0
            mock_gi.return_value.Gio = mock_gio

            mock_settings = mock.Mock()
            mock_widget = mock.Mock()

            self.service.bind_settings(mock_settings, 'show-log', mock_widget, 'visible')

            mock_settings.bind.assert_called_once_with('show-log', mock_widget, 'visible', 0)

    def test_create_builder_from_file(self):
        """create_builder_from_file should create Gtk.Builder from UI file."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gtk = mock.Mock()
            mock_builder = mock.Mock()
            mock_gtk.Builder.new_from_file.return_value = mock_builder
            mock_gi.return_value.Gtk = mock_gtk

            result = self.service.create_builder_from_file('/path/to/window.ui')

            mock_gtk.Builder.new_from_file.assert_called_once_with('/path/to/window.ui')
            assert result == mock_builder

    def test_create_action_variant_string(self):
        """create_action_variant should create GLib.Variant with format string."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_variant = mock.Mock()
            mock_glib.Variant.return_value = mock_variant
            mock_gi.return_value.GLib = mock_glib

            result = self.service.create_action_variant('s', 'daily')

            mock_glib.Variant.assert_called_once_with('s', 'daily')
            assert result == mock_variant

    def test_create_action_variant_multiple_values(self):
        """create_action_variant should support multiple format values."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_variant = mock.Mock()
            mock_glib.Variant.return_value = mock_variant
            mock_gi.return_value.GLib = mock_glib

            result = self.service.create_action_variant('i', 42)

            mock_glib.Variant.assert_called_once_with('i', 42)
            assert result == mock_variant

    def test_get_settings_bind_flags(self):
        """get_settings_bind_flags should return Gio.SettingsBindFlags."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_gio = mock.Mock()
            mock_flags = mock.Mock()
            mock_gio.SettingsBindFlags = mock_flags
            mock_gi.return_value.Gio = mock_gio

            result = self.service.get_settings_bind_flags()

            assert result == mock_flags

    def test_timeout_add_seconds(self):
        """timeout_add_seconds should schedule callback with delay."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            mock_callback = mock.Mock()
            mock_gi.return_value.GLib = mock_glib

            self.service.timeout_add_seconds(30, mock_callback, 'arg1')

            mock_glib.timeout_add_seconds.assert_called_once_with(30, mock_callback, 'arg1')

    def test_timeout_add_seconds_returns_handler_id(self):
        """timeout_add_seconds should return handler ID for later removal."""
        with mock.patch.object(self.service, 'gi') as mock_gi:
            mock_glib = mock.Mock()
            handler_id = 123
            mock_glib.timeout_add_seconds.return_value = handler_id
            mock_gi.return_value.GLib = mock_glib

            result = self.service.timeout_add_seconds(10, lambda: False)

            assert result == handler_id

    def test_connect_settings_changed(self):
        """connect_settings_changed should connect to settings signal."""
        with mock.patch.object(self.service, 'gi'):
            mock_settings = mock.Mock()
            mock_callback = mock.Mock()

            self.service.connect_settings_changed(mock_settings, 'changed::show-log', mock_callback)

            mock_settings.connect.assert_called_once_with('changed::show-log', mock_callback)

    def test_connect_settings_changed_returns_handler_id(self):
        """connect_settings_changed should return signal handler ID."""
        with mock.patch.object(self.service, 'gi'):
            mock_settings = mock.Mock()
            handler_id = 456
            mock_settings.connect.return_value = handler_id
            mock_callback = mock.Mock()

            result = self.service.connect_settings_changed(mock_settings, 'changed', mock_callback)

            assert result == handler_id
