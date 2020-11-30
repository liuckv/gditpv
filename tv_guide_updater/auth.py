import pycurl
import pycurl_requests as requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import urlunparse

from tv_guide_updater.utils.authenticator import Authenticator


class Auth:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.base_url = ''

    def authenticate(self):
        self.session = self.get_session()
        self.base_url = self.get_base_url()
        print('base_url: ' + self.base_url)
        cookies = self.login()
        print('cookies: ' + cookies)

    def get_session(self):
        session = requests.Session()
        session.curl.setopt(pycurl.INTERFACE, self.config['device']['iptv_interface'])
        session.curl.setopt(pycurl.COOKIEFILE, 'cookies.txt')
        session.curl.setopt(pycurl.COOKIEJAR, 'cookies.txt')
        session.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.0 (KHTML, like Gecko)'}
        return session

    def get_base_url(self):
        params = {'UserID': self.config['auth']['user_id'], 'Action': 'Login'}
        response = self.session.get(self.config['auth']['auth_url'], params=params, allow_redirects=False)
        url = response.headers.get('Location')
        # noinspection PyProtectedMember
        return urlunparse(urlparse(url)._replace(path='', query=''))

    def login(self):
        token = self.get_token()
        authenticator = Authenticator(self.config['auth']['encryption_key']).build(token,
                                                                                   self.config['auth']['user_id'],
                                                                                   self.config['device']['stb_id'],
                                                                                   self.config['device']['iptv_ip'],
                                                                                   self.config['device']['stb_mac'])
        data = {
            'UserID': self.config['auth']['user_id'],
            'Lang': '1',
            'SupportHD': '1',
            'NetUserID': self.config['auth']['net_user_id'],
            'Authenticator': authenticator,
            'STBType': 'EC6108V9U_pub_sccdx',
            'STBVersion': 'HWV207013P0000',
            'conntype': '4',
            'STBID': self.config['device']['stb_id'],
            'templateName': 'yszhibo',
            'areaId': '10105',
            'userToken': token,
            'userGroupId': '1',
            'productPackageId': '',
            'mac': self.config['device']['stb_mac'],
            'UserField': '2',
            'SoftwareVersion': 'V100R003C88LSCD07B013',
            'IsSmartStb': '0',
            'desktopId': '',
            'stbmaker': '',
            'VIP': ''
        }
        response = self.session.post(self.base_url + '/EPG/jsp/ValidAuthenticationHWCTC.jsp', data=data)
        return self.get_cookies_from_response(response)

    def get_token(self):
        data = {'UserID': self.config['auth']['user_id'], 'VIP': ''}
        response = self.session.post(self.base_url + '/EPG/jsp/authLoginHWCTC.jsp', data=data)
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find_all('script', string=re.compile('document.authform.userToken.value'))[0].string
        match = re.search(r'document.authform.userToken.value\s*=\s*\"(.+?)\"', script, re.MULTILINE)
        return match.group(1)

    @staticmethod
    def get_cookies_from_response(response):
        return response.headers.get('Set-Cookie')