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

class Project(FromJsonBlob):
    def __init__(self, api, name, customer,
                 number=None,
                 active=True,
                 billable_default=False,
                 budget_money=None,
                 budget_is_hours=False,
                 budget_is_not_strict=False,
                 note=None):
        self._api = api
        self.id = None
        self.name = name
        self.customers_id = customer.id
        self.number = number
        self.active = active
        self.billable_default = billable_default
        self.budget_money = budget_money
        self.budget_is_hours = budget_is_hours
        self.budget_is_not_strict = budget_is_not_strict
        self.note = note

    def note(self):
        if hasattr(self, "_note"):
            return self._note
        else:
            raise ClockodoError("You seem to lack privileges to view notes on projects.")

    def __str__(self):
        active = ""
        if not self.active:
            active = ", inactive"
        return f"{self.name} (project ID {self.id}{active}, for customer ID {self.customers_id})"


class ProjectApi(ClockodoApi):
    def get_project(self, id):
        entry = self._api_call(f"v2/projects/{id}")["project"]

    def list_projects(self, customer=None, active=None, page=None):
        response = self._api_call(f"v2/projects", params={
            "filter[active]": str(int(active)),
            "filter[customers_id]": customer.id if customer is not None else None,
            "page": page
        })
        response["projects"] = list(map(lambda c: Project.from_json_blob(self, c), response["projects"]))

        return response
