import requests

from requests.adapters import HTTPAdapter, Retry


class SessionManager:
    BASE_SITE_FOR_SESSION_URL = "https://www.ryanair.com/it/en"

    def __init__(self):
        self.session = requests.Session()
        self._set_retries()
        self._update_session_cookie()
    
    def _set_retries(self):
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[ 500, 502, 503, 504 ]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _update_session_cookie(self):
        # Visit main website to get session cookies
        self.session.get(self.BASE_SITE_FOR_SESSION_URL)

    def get_session(self):
        return self.session
