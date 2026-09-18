import unittest
from china_ppi_nowcast.ingest.nbs import is_challenge

class ChallengeTests(unittest.TestCase):
    def test_http_success_can_be_a_challenge(self):
        self.assertTrue(is_challenge(b'<noscript>Please enable JavaScript and refresh the page.</noscript>'))
        self.assertTrue(is_challenge('<noscript>请开启JavaScript并刷新该页.</noscript>'.encode()))
        self.assertFalse(is_challenge(b'<title>NBS release</title><table>prices</table>'))
