from __future__ import annotations

from typing import ClassVar

from gtimelog.models import Service

from ..models import ReportRecord, Reports


class ReportsService(Service):
    """Exposes report-related constants and classes."""

    _name = 'reports.service'
    Reports = Reports
    ReportRecord = ReportRecord
    REPORT_KINDS: ClassVar[dict] = {
        'day': ReportRecord.DAILY,
        'week': ReportRecord.WEEKLY,
        'month': ReportRecord.MONTHLY,
    }
