import requests

CLOCKODO_BASE_URL = "https://my.clockodo.com/api/"

class ClockodoError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"ClockodoError({self.msg})"


class ClockodoApiError(ClockodoError, Exception):
    def __init__(self, response):
        self.status = response.status
        try:
            self.data = response.json()
        except requests.exceptions.JSONDecodeError:
            self.data = None
        response.close()

    def __str__(self):
        return f"ClockodoApiError({self.status}, {self.data})"


class ClockodoApi:
    _ident = 'clockodo.py;oss@nyantec.com'

    def __init__(self, api_user, api_token, language='en'):
        self.user = api_user
        self.token = api_token
        self.language = language

    def _api_call(self, endpoint, method="GET", params=None):
        response = requests.request(
            method=method,
            url=CLOCKODO_BASE_URL + endpoint,
            data=None if method == "GET" else params,
            params=None if method != "GET" else params,
            headers={
                'X-ClockodoApiUser': self.user,
                'X-ClockodoApiKey': self.token,
                'X-Clockodo-External-Application': self._ident,
                'Accept-Language': self.language,
                'Accept': 'application/json',
            }
        )

        if response.ok:
            return response.json()
        else:
            raise ClockodoApiError(response)


class FromJsonBlob:
    _optional_fields = []
    _rename_fields = {}

    @classmethod
    def from_json_blob(cls, api, blob: dict):
        entry = cls.__new__(cls)
        for k, v in blob.items():
            setattr(entry, cls._rename_fields.get(k, k), v)
            entry._api = api
        for field in cls._optional_fields:
            if field not in blob:
                setattr(entry, field, None)

        return entry
