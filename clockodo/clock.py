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
from clockodo.entry import ClockEntry


class ClockApi(ClockodoApi):
    def current_clock(self):
        entry = self._api_call("v2/clock")["running"]
        if entry is None:
            return None
        assert entry["type"] == 1
        return ClockEntry.from_json_blob(self, entry)

    def stop_clock(self, clock: ClockEntry):
        if clock.time_until is not None:
            raise ClockodoError(f"this clock entry was already stopped at {clock.time_until}!")
        return self._api_call(f"v2/clock/{clock.id}", method="DELETE")

    def start_clock(self, clock: ClockEntry):
        return ClockEntry.from_json_blob(
            self,
            self._api_call(f"v2/clock", method="POST", params={
                "customers_id": clock.customers_id,
                "projects_id": clock.projects_id,
                "services_id": clock.services_id,
                "text": clock.text,
                "texts_id": clock.texts_id,
                "billable": str(int(clock.billable)) if clock.billable is not None else None
            })["running"]
        )
