import http.client
import unittest
from unittest.mock import MagicMock, call, patch
from china_ppi_nowcast.ingest.nbs import NBSClient


class FetchRetryTests(unittest.TestCase):
    def response(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'complete release'
        return response

    def test_disconnect_and_reset_retry_then_succeed(self):
        failures = [http.client.RemoteDisconnected('Remote end closed connection without response'),
                    ConnectionResetError('connection reset'), self.response()]
        with patch('urllib.request.urlopen', side_effect=failures) as fetch, \
             patch('china_ppi_nowcast.ingest.nbs.time.sleep') as sleep:
            self.assertEqual(NBSClient(retries=3).fetch('https://www.stats.gov.cn/test'), b'complete release')
            self.assertEqual(fetch.call_count, 3)
            self.assertEqual(sleep.call_args_list, [call(1), call(2)])

    def test_partial_body_is_discarded_and_retried(self):
        partial = self.response()
        partial.__enter__.return_value.read.side_effect = http.client.IncompleteRead(b'partial', 20)
        with patch('urllib.request.urlopen', side_effect=[partial, self.response()]) as fetch, \
             patch('china_ppi_nowcast.ingest.nbs.time.sleep'):
            self.assertEqual(NBSClient(retries=3).fetch('https://www.stats.gov.cn/test'), b'complete release')
            self.assertEqual(fetch.call_count, 2)

    def test_persistent_disconnect_remains_a_failure(self):
        error = http.client.RemoteDisconnected('closed')
        with patch('urllib.request.urlopen', side_effect=error) as fetch, \
             patch('china_ppi_nowcast.ingest.nbs.time.sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError, 'after 3 attempts') as raised:
                NBSClient(retries=3).fetch('https://www.stats.gov.cn/test')
            self.assertIs(raised.exception.__cause__, error)
            self.assertEqual(fetch.call_count, 3)
            self.assertEqual(sleep.call_count, 2)
