from gettext import gettext as _
import datetime
import re

from gtimelog.addons import registry as addons_registry
from gtimelog.core.ui.extensions import load_ui_with_extensions
from gtimelog.models import Controller, Service, component_registry
from gtimelog.paths import PREFERENCES_UI_FILE


def parse_time(value):
    """Parse a time value from 'HH:MM' formatted string."""
    match = re.match(r'^(\d+):(\d+)$', value)
    if not match:
        raise ValueError(f'bad time: {value!r}')
    hour, minute = map(int, match.groups())
    return datetime.time(hour, minute)


class PreferencesDialog:
    """Core preferences dialog (base settings + addon extension points)."""

    use_header_bar = None

    def __init__(self, transient_for, page=None):
        gi = Controller.gi()
        Gtk = gi.Gtk
        Gio = gi.Gio
        GLib = gi.GLib

        if self.use_header_bar is None:
            self.__class__.use_header_bar = hasattr(Gtk.DialogFlags, 'USE_HEADER_BAR')

        kwargs = {}
        if self.use_header_bar:
            kwargs['use_header_bar'] = True

        self.dialog = Gtk.Dialog(transient_for=transient_for, title=_('Preferences'), **kwargs)
        self.dialog.set_default_size(500, 0)

        if not self.use_header_bar:
            self.dialog.add_button(_('Close'), Gtk.ResponseType.CLOSE)
            self.dialog.set_default_response(Gtk.ResponseType.CLOSE)
        else:
            GLib.idle_add(self._make_enter_close_the_dialog)

        extended_ui = load_ui_with_extensions(PREFERENCES_UI_FILE, addons_registry)
        if extended_ui is not None:
            builder = Gtk.Builder.new_from_string(extended_ui, -1)
        else:
            builder = Gtk.Builder.new_from_file(PREFERENCES_UI_FILE)
        self.builder = builder
        stack = builder.get_object('dialog_stack')
        self.dialog.get_content_area().add(stack)
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        self.dialog.get_header_bar().set_custom_title(stack_switcher)
        stack_switcher.show()

        if page:
            stack.set_visible_child_name(page)

        self.gsettings = Gio.Settings.new('org.gtimelog')

        controller_cls = component_registry.get('prefs.controller')
        controller = controller_cls(self)
        controller.initialize(self)

    def run(self):
        self.dialog.connect('response', lambda *args: self.dialog.destroy())
        self.dialog.run()

    def get_transient_for(self):
        """Compatibility shim for addon controllers expecting dialog-like API."""
        return self.dialog.get_transient_for()

    def _make_enter_close_the_dialog(self):
        hb = self.dialog.get_header_bar()
        hb.forall(self._traverse_headerbar_children, None)

    def _traverse_headerbar_children(self, widget, _user_data):
        Gtk = Controller.gi().Gtk
        if isinstance(widget, Gtk.Box):
            widget.forall(self._traverse_headerbar_children, None)
        elif isinstance(widget, Gtk.Button) and widget.get_style_context().has_class('close'):
            widget.set_can_default(True)
            widget.grab_default()

    def __getattr__(self, name):
        """Delegate unknown attributes to wrapped Gtk.Dialog for addon compatibility."""
        return getattr(self.dialog, name)


class PreferencesApplicationService(Service):
    """Core service that opens the preferences dialog."""

    _name = 'application.preferences.service'

    @staticmethod
    def open_preferences(app, page=None):
        PreferencesDialog(app.get_active_window(), page=page).run()


class PreferencesController(Controller):
    """Core base preferences controller for base settings/widgets."""

    _name = 'prefs.controller'

    def __init__(self, dialog):
        super().__init__(dialog)

    def initialize(self, dialog):
        builder = dialog.builder
        gs = dialog.gsettings

        virtual_midnight_entry = builder.get_object('virtual_midnight_entry')
        rounding_time_entry = builder.get_object('rounding_time_entry')
        rounding_time_force_above_entry = builder.get_object('rounding_time_force_above_entry')

        if virtual_midnight_entry is None:
            return

        def _virtual_midnight_changed(*args):
            h, m = gs.get_value('virtual-midnight')
            virtual_midnight_entry.set_text(f'{h:d}:{m:02d}')

        def _virtual_midnight_set(*args):
            try:
                vm = parse_time(virtual_midnight_entry.get_text())
            except ValueError:
                _virtual_midnight_changed()
            else:
                h, m = gs.get_value('virtual-midnight')
                if (h, m) != (vm.hour, vm.minute):
                    gs.set_value('virtual-midnight', self.gi().GLib.Variant('(ii)', (vm.hour, vm.minute)))

        gs.connect('changed::virtual-midnight', _virtual_midnight_changed)
        _virtual_midnight_changed()
        virtual_midnight_entry.connect('focus-out-event', _virtual_midnight_set)

        if rounding_time_entry:
            gs.bind('rounding-time', rounding_time_entry, 'value', self.gi().Gio.SettingsBindFlags.DEFAULT)
        if rounding_time_force_above_entry:
            gs.bind(
                'rounding-time-force-above',
                rounding_time_force_above_entry,
                'active',
                self.gi().Gio.SettingsBindFlags.DEFAULT,
            )

        self._initialize_modules_page(builder, gs)

    def _initialize_modules_page(self, builder, gsettings):
        modules_list = builder.get_object('modules_list')
        modules_message_label = builder.get_object('modules_message_label')
        if modules_list is None:
            return

        # Keep addon metadata available even when preferences is opened early.
        addons_registry.discover(disabled_addons=gsettings.get_strv('disabled-addons'))

        module_service_cls = self.env['application.module.activation.service']
        module_service = module_service_cls(addons_registry)
        disabled_addons = set(gsettings.get_strv('disabled-addons'))

        switch_by_addon = {}
        state = {'updating': False}

        def show_info(message):
            if modules_message_label is None:
                return
            modules_message_label.set_text(message)
            modules_message_label.set_visible(bool(message))

        def sync_switches():
            state['updating'] = True
            for addon, module_switch in switch_by_addon.items():
                module_switch.set_active(addon not in disabled_addons)
            state['updating'] = False

        def on_switch_toggled(module_switch, _param, addon):
            if state['updating']:
                return
            active = bool(module_switch.get_active())
            effective_disabled, required_by = module_service.apply_toggle(addon, active, disabled_addons)
            if required_by:
                required_by_text = ', '.join(required_by)
                show_info(_('{0} is required by: {1}.').format(addon, required_by_text))
                sync_switches()
                return

            disabled_addons.clear()
            disabled_addons.update(effective_disabled)
            gsettings.set_strv('disabled-addons', sorted(disabled_addons))
            show_info(_('Module changes will apply after restarting the application.'))
            sync_switches()

        for addon in module_service.list_toggleable_modules():
            manifest = module_service.get_module_manifest(addon)
            title = manifest.get('name') or addon
            description = manifest.get('description') or ''

            row = self.gi().Gtk.ListBoxRow()
            row.set_visible(True)
            row.set_selectable(False)
            row.set_activatable(False)

            box = self.gi().Gtk.Box(orientation=self.gi().Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_border_width(8)
            box.set_visible(True)

            labels = self.gi().Gtk.Box(orientation=self.gi().Gtk.Orientation.VERTICAL, spacing=2)
            labels.set_hexpand(True)
            labels.set_visible(True)

            title_label = self.gi().Gtk.Label()
            title_label.set_xalign(0.0)
            title_label.set_markup(f'<b>{self.gi().GLib.markup_escape_text(title)}</b>')
            title_label.set_visible(True)

            labels.pack_start(title_label, False, False, 0)

            if description:
                description_label = self.gi().Gtk.Label()
                description_label.set_xalign(0.0)
                description_label.set_line_wrap(True)
                description_label.set_text(description)
                description_label.set_visible(True)
                labels.pack_start(description_label, False, False, 0)

            module_switch = self.gi().Gtk.Switch()
            module_switch.set_active(addon not in disabled_addons)
            module_switch.set_visible(True)
            module_switch.connect('notify::active', on_switch_toggled, addon)
            switch_by_addon[addon] = module_switch

            box.pack_start(labels, True, True, 0)
            box.pack_end(module_switch, False, False, 0)
            row.add(box)
            modules_list.add(row)

        sync_switches()
