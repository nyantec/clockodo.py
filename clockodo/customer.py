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

from clockodo.api import FromJsonBlob, ClockodoApi, ClockodoError

class Customer(FromJsonBlob):
    _rename_fields = {"note": "_note"}
    @classmethod
    def from_json_blob(cls, api, blob: dict):
        entry = super(Customer, cls).from_json_blob(api, blob)
        entry.billable_default = bool(entry.billable_default)

        return entry

    def __init__(self, api, name, number=None, active=True, billable_default=False, note=None):
        self._api = api
        self.id = None
        self.name = name
        self.number = number
        self.active = active
        self.billable_default = billable_default
        self._note = note

    def note(self):
        if hasattr(self, "_note"):
            return self._note
        else:
            raise ClockodoError("You seem to lack privileges to view notes on customers.")

    def __str__(self):
        active = ""
        if not self.active:
            active = ", inactive"
        return f"{self.name} (customer ID {self.id}{active})"


class CustomerApi(ClockodoApi):
    def get_customer(self, id):
        entry = self._api_call(f"v2/customers/{id}")["customer"]
        return Customer.from_json_blob(self, entry)

    def list_customers(self, active=None, page=None):
        response = self._api_call(f"v2/customers", params={
            "filter[active]": active,
            "page": page
        })
        response["customers"] = list(map(lambda c: Customer.from_json_blob(self, c), response["customers"]))

        return response
