# pylint: skip-file
import unittest
from unittest import mock

import sanitizer_utils


class TestSanitizer(unittest.TestCase):
    """Ensure sanitizer works properly"""
    @mock.patch('requests.get')
    def test_redirect(self, mock_request):
        mock_request.return_value = mock.Mock(status_code=200, url='https://google.com')
        self.assertEqual(sanitizer_utils.handle_redirect('https://example.com'),
                         'https://example.com')
        mock_request.assert_not_called()
        self.assertEqual(sanitizer_utils.handle_redirect('https://a.co/whatever'),
                         'https://google.com')

    def test_proxy_if_necessary(self):
        self.assertEqual(sanitizer_utils.proxy_if_necessary('https://google.com'),
                         ('https://google.com', False))
        self.assertEqual(sanitizer_utils.proxy_if_necessary('https://x.com'),
                         ('https://fixupx.com', True))

    @mock.patch('requests.get')
    def test_sanitize_message(self, mock_request):
        mock_request.return_value = mock.Mock(status_code=200, url='https://fixupx.com', text='only text here')
        content = 'https://x.com/minkbazink/status/1802192921086820534?s=19'
        self.assertEqual(sanitizer_utils.sanitize_message(content),
                         ('', False, False))
        mock_request.assert_called()
        mock_request.reset_mock()

        mock_request.return_value = mock.Mock(status_code=200, url='https://fixupx.com', text='mp4 is here')
        self.assertEqual(sanitizer_utils.sanitize_message(content),
                         ('https://fixupx.com/minkbazink/status/1802192921086820534?s=19', True, False))
        mock_request.assert_called()
        mock_request.reset_mock()

        content = 'https://www.aliexpress.us/item/3256807014020439.html?gps-id=pcStoreJustForYou&scm=1007.23125.137358'\
                  '.0&scm_id=1007.23125.137358.0&scm-url=1007.23125.137358.0&pvid=eb121b6f-264a-457f-9d94-15eca51c3017'
        mock_request.reset_mock()
        self.assertEqual(sanitizer_utils.sanitize_message(content),
                         ('<https://www.aliexpress.us/item/3256807014020439.html>', True, True))
        mock_request.assert_not_called()

    def test_sanitize_url(self):
        self.assertEqual(sanitizer_utils.sanitize_url('https://google.com'),
                         'https://google.com', False)
        self.assertEqual(sanitizer_utils.sanitize_url('https://drop.com/buy/drop-ctrl-v2-mechanical-keyboard?mode=shop_'
                                                      'open&defaultSelectionIds=981286%2C981288&utm_source=google&utm_m'
                                                      'edium=cpc&utm_campaign=20546672575&utm_term=&utm_content=&utm_ke'
                                                      'yword=&utm_placement=&utm_network=x:c::&utm_device=&mode=shop_op'
                                                      'en&gad_source=1&gclid=CjwKCAjwko21BhAPEiwAwfaQCPCsx4JPAYJViGM7Wl'
                                                      'j6pmlJPDVstBL0B4oFosvmEr0VFAYAoDBoIhoCL10QAvD_BwE&gclsrc=aw.ds'),
                         'https://drop.com/buy/drop-ctrl-v2-mechanical-keyboard?defaultSelectionIds=981286%2C981288')
        self.assertEqual(sanitizer_utils.sanitize_url('https://x.com/testwhatever/status/20938409238423042?t=i&asdf=jlk'),
                         'https://x.com/testwhatever/status/20938409238423042?t=i')
