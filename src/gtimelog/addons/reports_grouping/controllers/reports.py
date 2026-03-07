import datetime

from gtimelog.models import Controller


class Reports(Controller):
    """Extend reports plain mode with customer/project/task grouping."""

    _name = None
    _inherit = 'reports'

    def __init__(self, window, email_headers=True, style='plain'):
        super().__init__(window, email_headers=email_headers, style=style)
        self.reports_app_service = self.env.get('application.reports.service')

    def parse_entry_line(self, entry):
        return self.reports_app_service.parse_entry_line(entry)

    def _customer_tasks_table(self, output, distribute_slack=False, proportional=True):
        """Generate a structured list of tasks grouped by customer/project/category."""
        work, _slack = self.window.grouped_entries(
            distribute_slack=distribute_slack,
            proportional=proportional,
        )
        if not work:
            output.write('No work entries found.\n')
            return

        errors, customer_tree = self._build_customer_tree(work)
        for err in errors:
            output.write(f'ERROR: {err}\n')
        self._render_customer_tree(output, customer_tree)

    def _build_customer_tree(self, work_entries):
        """Build a nested dict: customer → project → category → task_key → (desc, duration)."""
        return self.reports_app_service.build_customer_tree(work_entries)

    def _render_customer_tree(self, output, customer_tree):
        service = self.env.get('application.reports.service')
        return service.render_customer_tree(output, customer_tree)

    def _plain_report(self, output, email, who, subject, period_name):
        """Format a grouped plain report (customer/project/task)."""
        window = self.window

        if self.email_headers:
            output.write(f'To: {email}\n')
            output.write(f'Subject: {subject}\n')
            output.write('\n')

        items = list(window.all_entries())
        if not items:
            output.write(f'No work done this {period_name}.\n')
            return
        output.write(' ' * 46)
        output.write('                time\n')
        work, _slack = window.grouped_entries(
            distribute_slack=self.distribute_slack,
            proportional=self.proportional,
        )
        total_work = sum((duration for _start, _entry, duration in work), datetime.timedelta(0))
        self._customer_tasks_table(
            output,
            distribute_slack=self.distribute_slack,
            proportional=self.proportional,
        )
        output.write(
            f'Total work done this {period_name}: {self.duration_formatter.format_duration_long(total_work)}\n'
        )

        tags = self.window.set_of_all_tags()
        if tags:
            self._report_tags(output, tags)
