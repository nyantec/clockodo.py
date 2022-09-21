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

class ClockEntry(FromJsonBlob):
    _rename_fields = {"text": "_text"}

    @classmethod
    def from_json_blob(cls, api, blob: dict):
        entry = super(ClockEntry, cls).from_json_blob(api, blob)
        entry.billable = bool(entry.billable)

        return entry

    def __init__(self, api, customer, service,
                 texts_id=None, text=None,
                 project=None,
                 billable=False,
                 time_since=None, time_until=None):
        if texts_id is None and text is None:
            raise ClockodoError("One of texts_id or text should be specified!")
        self._api = api
        self.customers_id = customer.id
        self.services_id = service.id
        self.texts_id = texts_id
        self._text = text
        self.projects_id = project.id if project is not None else None
        self.billable = billable
        self.time_since = time_since
        self.time_until = time_until
        # These are filled by clocko:do
        self.time_insert = None
        self.time_last_change = None

    def customer(self):
        return self._api.get_customer(self.customers_id)

    def project(self):
        if self.projects_id is None:
            return None
        return self._api.get_project(self.projects_id)

    def service(self):
        return self._api.get_service(self.services_id)

    def text(self):
        return self._text


class ClockApi(ClockodoApi):
    def current_clock(self):
        entry = self._api_call("v2/clock")["running"]
        assert entry["type"] == 1
        return ClockEntry.from_json_blob(self, entry)

    def stop_clock(self, clock: ClockEntry):
        return self._api_call(f"v2/clock/{clock.id}", method="DELETE")

    def start_clock(self, clock: ClockEntry):
        if clock.time_until is not None:
            raise ClockodoError(f"this clock entry was already stopped at {clock.time_until}!")
        return self._api_call(f"v2/clock", method="POST", params={
            customers_id: clock.customers_id,
            projects_id: clock.projects_id,
            services_id: clock.services_id,
            text: clock.text,
            texts_id: clock.texts_id,
            billable: str(int(billable))
        })
