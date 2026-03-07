{
    'name': 'Reports iCalendar',
    'version': '1.0.0',
    'description': 'iCalendar export format for time log entries.',
    'author': 'GTimeLog Contributors',
    'module_type': 'functional',
    'layer': 'integration',
    'domain': 'export_ical',
    'depends': ['reports'],
    'views': [
        'views/gtimelog.ui.xml',
        'views/preferences.ui.xml',
    ],
}
