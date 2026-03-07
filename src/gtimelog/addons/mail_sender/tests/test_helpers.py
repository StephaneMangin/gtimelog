import unittest
from unittest import mock

from gtimelog.addons.mail_sender.models.email import MAIL_PROTOCOLS, address_header, prepare_message, subject_header

gi = mock.MagicMock()
gi.repository.Gtk.MAJOR_VERSION = 3
gi.repository.Gtk.MINOR_VERSION = 3
mock_gi = mock.patch.dict('sys.modules', {'gi': gi, 'gi.repository': gi.repository})


@mock_gi
class TestAddressHeader(unittest.TestCase):
    def test_ascii_passthrough(self):
        assert address_header('John Doe <john@example.com>') == 'John Doe <john@example.com>'

    def test_unicode_encoded(self):
        result = address_header('Unicod Name <test@example.com>')
        assert 'test@example.com' in result

    def test_plain_address(self):
        assert address_header('test@example.com') == 'test@example.com'


@mock_gi
class TestSubjectHeader(unittest.TestCase):
    def test_ascii_passthrough(self):
        assert subject_header('Weekly report') == 'Weekly report'

    def test_unicode_encoded(self):
        result = subject_header('Rapport hebd')
        assert result is not None


@mock_gi
class TestPrepareMessage(unittest.TestCase):
    def test_plain_text(self):
        msg = prepare_message('a@b.com', 'c@d.com', 'Test', 'body text')
        assert msg['Subject'] == 'Test'
        assert msg['To'] == 'c@d.com'
        assert msg['From'] == 'a@b.com'
        assert 'gtimelog/' in msg['User-Agent']
        assert 'body text' in msg.as_string()

    def test_no_sender(self):
        msg = prepare_message(None, 'c@d.com', 'Test', 'body')
        assert msg['From'] is None

    def test_empty_body(self):
        msg = prepare_message('a@b.com', 'c@d.com', 'Test', '')
        assert 'Test' in msg['Subject']

    def test_csv_attachment(self):
        csv_data = 'col1,col2\nval1,val2\n'
        msg = prepare_message(
            'a@b.com',
            'c@d.com',
            'Report',
            'See attached.',
            csv_attachment=('report.csv', csv_data),
        )
        assert msg.is_multipart()
        parts = msg.get_payload()
        assert len(parts) == 2
        assert 'See attached' in parts[0].get_payload()
        assert parts[1].get_filename() == 'report.csv'

    def test_csv_attachment_content_type(self):
        msg = prepare_message(
            'a@b.com',
            'c@d.com',
            'Test',
            'body',
            csv_attachment=('data.csv', 'a,b\n1,2\n'),
        )
        csv_part = msg.get_payload()[1]
        assert csv_part.get_content_type() == 'text/csv'


@mock_gi
class TestMailProtocols(unittest.TestCase):
    def test_protocols_defined(self):
        assert 'SMTP' in MAIL_PROTOCOLS
        assert 'SMTPS' in MAIL_PROTOCOLS
        assert 'SMTP (StartTLS)' in MAIL_PROTOCOLS

    def test_protocol_structure(self):
        for _, proto in MAIL_PROTOCOLS.items():
            assert callable(proto.factory)
            assert isinstance(proto.startssl, bool)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
