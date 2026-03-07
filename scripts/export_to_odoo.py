#!/usr/bin/env python3

import argparse
import os
import re
import xmlrpc.client
from datetime import datetime

ODOO_URL = 'https://my.acsone.eu/'
ODOO_EXT_DB = 'odoo'
ODOO_USER = 'stephane.mangin@acsone.eu'
CUSTOMER = 'ACSONE'
ODOO_API_KEY = '7b0db1ab15b52a26e3b7f72fe77a7b0ac1101601'


def get_gtimelog_tasks_file() -> str:
    """
    Détermine le chemin standard du fichier tasks.txt de GTimeLog.
    Reproduit la logique de src/gtimelog/settings.py :
    1. Variable GTIMELOG_HOME si définie
    2. Dossier legacy ~/.gtimelog si existant
    3. Standard XDG (XDG_DATA_HOME/gtimelog ou ~/.local/share/gtimelog)
    """
    # 1. ENV GTIMELOG_HOME
    env_home = os.environ.get('GTIMELOG_HOME')
    if env_home:
        return os.path.join(os.path.expanduser(env_home), 'timelog.txt')

    # 2. Dossier Legacy
    legacy_default = os.path.expanduser('~/.gtimelog')
    if os.path.isdir(legacy_default):
        return os.path.join(legacy_default, 'timelog.txt')

    # 3. Standard XDG Data
    xdg_data_home = os.environ.get('XDG_DATA_HOME') or '~/.local/share'
    return os.path.join(os.path.expanduser(xdg_data_home), 'gtimelog', 'timelog.txt')


# configuration class to manage settings and defaults
class config_manager:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='import odoo 18 timesheets')
        self._setup_options()
        self.args = self.parser.parse_args()

    def _setup_options(self):
        # odoo connection defaults as requested
        self.parser.add_argument('--url', default=os.environ.get('ODOO_URL', ODOO_URL), help='odoo instance url')
        self.parser.add_argument('--db', default=os.environ.get('ODOO_EXT_DB', ODOO_EXT_DB), help='database name')
        self.parser.add_argument('--user', default=os.environ.get('ODOO_USER', ODOO_USER), help='odoo username')
        self.parser.add_argument('--api-key', default=os.environ.get('ODOO_API_KEY', ODOO_API_KEY), help='odoo api key')

        # logic and file settings
        self.parser.add_argument(
            '--file', default=os.environ.get('TASK_INPUT_FILE', get_gtimelog_tasks_file()), help='path to log file'
        )
        self.parser.add_argument('--customer', default=os.environ.get('CUSTOMER', CUSTOMER), help='customer to export')
        self.parser.add_argument('--dry-run', action='store_true', help='parse and calculate without sending to odoo')

        # semaine à synchroniser
        self.parser.add_argument(
            '--week',
            type=int,
            help='week number to process (default: current week)',
            default=datetime.now().isocalendar().week,
        )

    def get_values(self):
        return self.args


# odoo rpc client handler
class odoo_api:
    def __init__(self, url, db, user, api_key):
        self.url = url.rstrip('/')
        self.db = db
        self.user = user
        self.uid = None
        self.api_key = api_key
        self.models = None

    def connect(self):
        """Authenticate with Odoo using XML-RPC (supports API keys)"""
        try:
            # Use XML-RPC for authentication as it properly supports API keys
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')

            # Get version info first to verify connectivity
            try:
                version_info = common.version()
                print(f'Connected to Odoo {version_info.get("server_version", "unknown")}')
            except Exception as e:
                raise Exception(f'Cannot connect to Odoo server: {e}')

            # Authenticate with API key
            try:
                self.uid = common.authenticate(self.db, self.user, self.api_key, {})
            except Exception as auth_error:
                raise Exception(f'Authentication error: {auth_error}')

            if not self.uid:
                raise Exception(
                    f'Authentication failed - invalid credentials.\n'
                    f'  Database: {self.db}\n'
                    f'  User: {self.user}\n'
                    f'  API Key: {"*" * (len(self.api_key) - 4)}{self.api_key[-4:] if len(self.api_key) > 4 else "***"}\n'
                    f'Please verify:\n'
                    f'  1. The API key is valid and not expired\n'
                    f'  2. The user exists in the database\n'
                    f'  3. The database name is correct'
                )

            print(f'Authenticated as user ID: {self.uid}')

            # Initialize models proxy for subsequent API calls
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            return True

        except Exception as e:
            raise Exception(f'Connection failed: {e}')

    def execute_kw(self, model, method, args=None, kwargs=None):
        """Execute a model method via XML-RPC"""
        if not self.models:
            raise Exception('Not connected - call connect() first')

        # XML-RPC signature: execute_kw(db, uid, password, model, method, args, kwargs)
        if kwargs:
            return self.models.execute_kw(self.db, self.uid, self.api_key, model, method, args or [], kwargs)
        return self.models.execute_kw(self.db, self.uid, self.api_key, model, method, args or [])

    def find_id(self, model, name, extra_domain=None):
        domain = [('name', '=', name)]
        if extra_domain:
            domain += extra_domain

        result = self.execute_kw(model, 'search', args=[domain], kwargs={'limit': 1})
        return result[0] if result else None

    def create_timesheet(self, project_id, task_id, description, date, hours):
        values = {
            'project_id': project_id,
            'task_id': task_id,
            'name': description,
            'date': date,
            'unit_amount': hours,
        }
        return self.execute_kw('account.analytic.line', 'create', args=[values])

    def update_timesheet(self, timesheet_id, hours):
        return self.execute_kw('account.analytic.line', 'write', args=[[timesheet_id], {'unit_amount': hours}])

    def upsert_timesheet(self, project_id, task_id, description, date, hours, project_name):
        """
        Create or update a timesheet entry.
        Returns a tuple (action, message) where action is 'updated', 'created', or 'skipped'
        """
        if hours <= 0:
            return ('skipped', f'skipped: hours={hours:.2f}h is not positive')

        # Check if timesheet already exists
        timesheet_id = self.find_id(
            'account.analytic.line',
            description,
            [('project_id', '=', project_id), ('task_id', '=', task_id), ('date', '=', date)],
        )

        if timesheet_id:
            self.update_timesheet(timesheet_id, hours)
            return ('updated', f'updated: added {hours:.2f}h to existing timesheet on {project_name}')
        self.create_timesheet(project_id, task_id, description, date, hours)
        return ('created', f'success: logged {hours:.2f}h on {project_name}')


def main():
    config = config_manager()
    args = config.get_values()

    if not os.path.exists(args.file):
        print(f'error: file {args.file} not found')
        return

    # regex to capture components based on your requirements
    # matches: {date} {time}: {customer}: {project} / {task} -> {description} / ...
    pattern = re.compile(
        r'^(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}): (?P<cust>[^:]+): (?P<proj>[^/]+) / (?P<task>[^/]+) -> (?P<desc>#\d+ .+?) /'
    )

    print(args.url, args.db, args.user, args.api_key)
    api = odoo_api(args.url, args.db, args.user, args.api_key)
    if not api.connect():
        print('failed to connect to odoo')
        return
    print('connected to odoo')

    last_dt = None

    with open(args.file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            print(f'processing line: {line}')

            # try to extract timestamp from the start of every line to track elapsed time
            try:
                current_dt_str = line[:16]
                current_dt = datetime.strptime(current_dt_str, '%Y-%m-%d %H:%M')
                # filter by week if specified
                if args.week and current_dt.isocalendar().week != args.week:
                    continue
            except ValueError:
                continue

            match = pattern.match(line)
            if match:
                customer = match.group('cust').strip()
                project_name = match.group('proj').strip()
                task_name = match.group('task').strip()
                description = match.group('desc').strip()

                # rule: do not process if customer matches the exclusion variable
                if customer != args.customer:
                    last_dt = current_dt
                    continue

                # calculate duration based on the gap with the previous line
                if last_dt:
                    diff = current_dt - last_dt
                    hours = diff.total_seconds() / 3600.0

                    if hours > 0:
                        entry_date = current_dt.strftime('%Y-%m-%d')
                        # odoo search and create
                        p_id = api.find_id('project.project', project_name)
                        if p_id:
                            t_id = api.find_id('project.task', task_name, [('project_id', '=', p_id)])
                            if t_id:
                                print(f'Processing task {task_name} on {entry_date} (duration: {hours:.2f}h)')
                                if not args.dry_run:
                                    action, message = api.upsert_timesheet(
                                        p_id, t_id, description, entry_date, hours, project_name
                                    )
                                    print(message)
                        else:
                            print(f"skipped: project '{project_name}' not found")

            # update last timestamp for the next iteration (even for break/arrived lines)
            last_dt = current_dt


if __name__ == '__main__':
    main()
