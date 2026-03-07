import datetime

from gtimelog.models import Service, component_registry


class ReportsDomainService(Service):
    """Domain service for parsing and structuring report entries."""

    _name = 'domain.reports.service'

    def __init__(self, entry_parser=None, duration_formatter=None):
        self.entry_parser = entry_parser or component_registry.get('platform.entry.parser')()
        self.duration_formatter = duration_formatter or component_registry.get('platform.duration.formatter')()

    def parse_entry_line(self, entry):
        result = {
            'customer': None,
            'ref': None,
            'project': None,
            'phase': None,
            'task': None,
            'title': None,
            'comment': None,
            'raw': entry,
            'error': True,
        }

        if not entry or not isinstance(entry, str):
            return result

        try:
            entry_obj = self.entry_parser.parse(entry)
            return {
                'customer': entry_obj.get('customer'),
                'ref': entry_obj.get('ref'),
                'project': entry_obj.get('project'),
                'phase': entry_obj.get('phase'),
                'task': entry_obj.get('task'),
                'title': entry_obj.get('title'),
                'comment': entry_obj.get('comment'),
                'raw': entry,
                'error': entry_obj.get('customer') is None,
            }
        except Exception:
            return result

    def build_customer_tree(self, work_entries):
        errors = []
        tree = {}

        for _start, entry, duration in work_entries:
            if not duration:
                continue

            parsed = self.parse_entry_line(entry)
            if parsed['error']:
                errors.append(entry)
            if not parsed['customer']:
                continue

            customer = parsed['customer']
            project_name = parsed['project'] or 'Sans projet'
            project = f'[{parsed["ref"]}] {project_name}' if parsed['ref'] else project_name
            category = parsed['phase'] or 'Sans catégorie'

            task_key = '|'.join([parsed['task'] or '', parsed['title'] or ''])
            task_parts = []
            if parsed['task']:
                task_parts.append(f'#{parsed["task"]}')
            if parsed['title']:
                task_parts.append(parsed['title'])
            task_desc = ' '.join(task_parts) if task_parts else entry

            tasks_dict = tree.setdefault(customer, {}).setdefault(project, {}).setdefault(category, {})
            if task_key in tasks_dict:
                tasks_dict[task_key] = (tasks_dict[task_key][0], tasks_dict[task_key][1] + duration)
            else:
                tasks_dict[task_key] = (task_desc, duration)

        return errors, tree

    def render_customer_tree(self, output, customer_tree):
        output.write('\n')
        output.write('SUMMARY OF TASKS BY CLIENTS\n')
        output.write('-' * 110 + '\n')

        total_all = datetime.timedelta(0)

        for customer in sorted(customer_tree):
            total_customer = sum(
                (
                    dur
                    for projects in customer_tree[customer].values()
                    for tasks in projects.values()
                    for _, dur in tasks.values()
                ),
                datetime.timedelta(0),
            )
            total_all += total_customer

            total_customer_fmt = self.duration_formatter.format_duration_long(total_customer)
            output.write(f'\n{customer.upper()} ({total_customer_fmt})\n')
            output.write('-' * len(f'{customer} ({total_customer_fmt})') + '\n')

            for project in sorted(customer_tree[customer]):
                categories_dict = customer_tree[customer][project]
                total_project = sum(
                    (dur for tasks in categories_dict.values() for _, dur in tasks.values()),
                    datetime.timedelta(0),
                )
                output.write(f'\n  {project} ({self.duration_formatter.format_duration_short(total_project)})\n')

                for category in sorted(categories_dict):
                    tasks_dict = categories_dict[category]
                    total_category = sum((dur for _, dur in tasks_dict.values()), datetime.timedelta(0))
                    total_category_fmt = self.duration_formatter.format_duration_short(total_category)
                    output.write(f'    > {category} ({total_category_fmt}):\n')

                    for desc, dur in sorted(tasks_dict.values(), key=lambda x: x[0]):
                        output.write(f'      - {desc:<90}  {self.duration_formatter.format_duration_short(dur):>6}\n')

        output.write('-' * 110 + '\n')
        output.write(f'TOTAL {self.duration_formatter.format_duration_short(total_all):>100}\n')
