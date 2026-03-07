import os

from gtimelog import __version__
from gtimelog.models import Service
from gtimelog.paths import ABOUT_DIALOG_UI_FILE, CONTRIBUTORS_FILE, ICON_LARGE_FILE


class AboutApplicationService(Service):
    """Core application service for About dialog rendering."""

    _name = 'application.about.service'

    @staticmethod
    def get_contributors():
        contributors = []
        with open(CONTRIBUTORS_FILE, encoding='utf-8') as f:
            for line in f:
                if line.startswith('- '):
                    contributors.append(line[2:].strip())
        return sorted(contributors)

    def show_about_dialog(self, app):
        app_service = self.env.get('application.service')

        builder = app_service.create_builder_from_file(ABOUT_DIALOG_UI_FILE)
        about_dialog = builder.get_object('about_dialog')
        about_dialog.set_version(__version__)
        if os.path.exists(ICON_LARGE_FILE):
            about_dialog.set_logo(self.gi().GdkPixbuf.Pixbuf.new_from_file(ICON_LARGE_FILE))
        about_dialog.set_authors(self.get_contributors())
        about_dialog.set_transient_for(app.get_active_window())
        about_dialog.connect('response', lambda *args: about_dialog.destroy())
        about_dialog.show()
