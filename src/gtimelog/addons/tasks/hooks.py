from gtimelog.models import Hook


class TasksHooks(Hook):
    """Tasks addon hooks.

    All initialization hooks have been migrated to Controllers:
    - window_init → TasksWindowController
    - app_startup → TasksApplicationController
    - settings_migration → TasksSettingsMigrator
    """
