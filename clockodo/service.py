# Copyright © 2022 nyantec GmbH <oss@nyantec.com>
# Written by Vika Shleina <vsh@nyantec.com>
#
# Provided that these terms and disclaimer and all copyright notices
# are retained or reproduced in an accompanying document, permission
# is granted to deal in this work without restriction, including un‐
# limited rights to use, publicly perform, distribute, sell, modify,
# merge, give away, or sublicence.
#
# This work is provided "AS IS" and WITHOUT WARRANTY of any kind, to
# the utmost extent permitted by applicable law, neither express nor
# implied; without malicious intent or gross negligence. In no event
# may a licensor, author or contributor be held liable for indirect,
# direct, other damage, loss, or other issues arising in any way out
# of dealing in the work, even if advised of the possibility of such
# damage or existence of a defect, except proven that it results out
# of said person's immediate fault when using the work as intended.

from clockodo.api import FromJsonBlob, ClockodoApi

class Service(FromJsonBlob):
    def __init__(self, api, name, number=None, active=True, note=None):
        self._api = None
        self.name = name
        self.number = number
        self.active = active
        self.note = note

    def __str__(self):
        active = ""
        if not self.active:
            active = ", inactive"
        return f"{self.name} (service ID {self.id}{active})"


class ServiceApi(ClockodoApi):
    def get_service(self, id):
        entry = self._api_call(f"services/{id}")["service"]
        return Service.from_json_blob(self, entry)

    def list_services(self, page=None):
        response = self._api_call(f"services")
        response["services"] = list(map(lambda s: Service.from_json_blob(self, s), response["services"]))

        return response
