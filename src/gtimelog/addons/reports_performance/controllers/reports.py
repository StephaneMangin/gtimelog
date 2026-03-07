from gtimelog.models import Controller


class Reports(Controller):
    """Extend reports with a performance-focused rendering style."""

    _inherit = 'reports'

    def __init__(self, window, email_headers=True, style='plain'):
        super().__init__(window, email_headers=email_headers, style=style)
        self.metrics_service = self.env.get('reports.performance.metrics')

    @staticmethod
    def _percent(value: float) -> str:
        return f'{value * 100:.1f}%'

    def _render_top_clients(self, output, top_clients):
        output.write('TOP 5 CLIENTS\n')
        if not top_clients:
            output.write('- No billable client entries for this period.\n')
            return

        for index, (name, duration) in enumerate(top_clients, start=1):
            output.write(
                f'- {index}. {name:<30s} {self.duration_formatter.format_duration_short(duration):>6s}\n'
            )

    def _performance_subject(self, who, period_name):
        return f'{period_name} performance report for {who}'

    def _performance_report(self, output, email, who, subject, period_name):
        if self.email_headers:
            output.write(f'To: {email}\n')
            output.write(f'Subject: {subject}\n')
            output.write('\n')

        metrics = self.metrics_service.compute(
            self.window,
            distribute_slack=self.distribute_slack,
            proportional=self.proportional,
        )

        output.write('PERFORMANCE SUMMARY\n')
        output.write(f'- Period: {period_name}\n')
        output.write(f'- Total worked: {self.duration_formatter.format_duration_long(metrics["total_work"])}\n')
        output.write(
            f'- Billable: {self.duration_formatter.format_duration_long(metrics["billable"])} '
            f'({self._percent(metrics["billable_rate"])})\n'
        )
        output.write(
            f'- Non-billable: {self.duration_formatter.format_duration_long(metrics["non_billable"])} '
            f'({self._percent(metrics["non_billable_rate"])})\n'
        )
        output.write(
            f'- Slack: {self.duration_formatter.format_duration_long(metrics["total_slack"])} '
            f'({self._percent(metrics["slack_rate"])} of observed total)\n'
        )
        output.write(
            f'- Productive utilization: {self._percent(metrics["productive_utilization_rate"])}\n'
        )

        output.write('\nFOCUS AND EFFICIENCY\n')
        if metrics['top_client_name']:
            output.write(
                f'- Top client: {metrics["top_client_name"]} '
                f'({self.duration_formatter.format_duration_long(metrics["top_client_duration"])}, '
                f'{self._percent(metrics["top_client_share"])} of billable)\n'
            )
        else:
            output.write('- Top client: n/a\n')
        output.write(f'- Active clients: {metrics["active_clients"]}\n')
        output.write(f'- Active tasks: {metrics["active_tasks"]}\n')
        output.write(
            f'- Average billable session: '
            f'{self.duration_formatter.format_duration_long(metrics["avg_billable_session"])}\n'
        )

        output.write('\n')
        self._render_top_clients(output, metrics['top_clients'])

    def weekly_report(self, output, email, who):
        if self.style != 'performance':
            return super().weekly_report(output, email, who)
        subject = self._performance_subject(who, 'Weekly')
        return self._performance_report(output, email, who, subject, 'week')

    def monthly_report(self, output, email, who):
        if self.style != 'performance':
            return super().monthly_report(output, email, who)
        subject = self._performance_subject(who, 'Monthly')
        return self._performance_report(output, email, who, subject, 'month')

    def daily_report(self, output, email, who):
        if self.style != 'performance':
            return super().daily_report(output, email, who)
        subject = self._performance_subject(who, 'Daily')
        return self._performance_report(output, email, who, subject, 'day')
