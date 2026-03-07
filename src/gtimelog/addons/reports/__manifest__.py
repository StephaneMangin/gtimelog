{
    'name': 'Reports',
    'version': '1.0.0',
    'description': 'Report generation and ReportView widget for GTimeLog.',
    'author': 'GTimeLog Contributors',
    'module_type': 'functional',
    'layer': 'feature',
    'domain': 'reporting',
    'depends': ['timelog'],
    'views': [
        'views/gtimelog.ui.xml',
        'views/menus.ui.xml',
        'views/preferences.ui.xml',
        'views/shortcuts.ui.xml',
    ],
}
