import datetime
from abc import ABCMeta, abstractmethod
from clockodo.api import FromJsonBlob, ClockodoApi

ISO8601_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

def format_timedelta(timedelta):
    hours, rem = divmod(timedelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if timedelta.days > 0:
        d = "{}d, ".format(timedelta.days)
    else:
        d = ""
    return "{d}{hours}h{minutes}m".format(
        d=d, hours=hours, minutes=minutes
    )


def iso8601(dt: datetime.datetime) -> str:
    # Normalize datetime to UTC
    # It's the only timezone clocko:do understands apparently
    if dt.tzinfo != datetime.timezone.utc:
        dt = dt.replace(tzinfo=datetime.timezone.utc) - dt.utcoffset()
    dt = dt.strftime(ISO8601_TIME_FORMAT)
    if dt.endswith("+0000"):
        dt = dt.removesuffix("+0000") + "Z"
    return dt


class BaseEntry(metaclass=ABCMeta):
    @classmethod
    def from_json_blob(cls, api, blob: dict):
        if blob["type"] == 1:
            return ClockEntry.from_json_blob(api, blob)
        elif blob["type"] == 2:
            return LumpSumValue.from_json_blob(api, blob)
        elif blob["type"] == 3:
            return EntryWithLumpSumService.from_json_blob(api, blob)
        else:
            raise ClockodoError("clocko:do returned entry with unknown type " + str(blob["type"]))

    def edit(self, edit: dict):
        return self._api.edit_entry(self, edit)


class ClockEntry(FromJsonBlob, BaseEntry):
    _rename_fields = {}

    @classmethod
    def from_json_blob(cls, api, blob: dict):
        entry = super(ClockEntry, cls).from_json_blob(api, blob)
        entry.billable = bool(entry.billable)
        if entry.time_until is not None:
            entry.time_until = datetime.datetime.strptime(entry.time_until, ISO8601_TIME_FORMAT)
        entry.time_since = datetime.datetime.strptime(entry.time_since, ISO8601_TIME_FORMAT)

        return entry

    def __init__(self, api, customer, service,
                 time_since=None, time_until=None,
                 texts_id=None, text=None,
                 project=None,
                 billable=False,
                 hourly_rate=None):
        self.type = 1
        if texts_id is None and text is None:
            raise ClockodoError("One of texts_id or text should be specified!")
        self._api = api
        self.customers_id = customer.id
        self.services_id = service.id
        self.texts_id = texts_id
        self.text = text
        self.projects_id = project.id if project is not None else None
        self.billable = billable
        self.time_since = time_since
        self.time_until = time_until
        # These are filled by clocko:do
        self.time_insert = None
        self.time_last_change = None
        self.clocked = None
        self.clocked_offline = None
        self.time_clocked_since = None
        self.time_last_change_worktime = None
        self.duration = None
        self.hourly_rate = hourly_rate

    def customer(self):
        return self._api.get_customer(self.customers_id)

    def project(self):
        if self.projects_id is None:
            return None
        return self._api.get_project(self.projects_id)

    def service(self):
        return self._api.get_service(self.services_id)

    def clock_duration(self) -> datetime.timedelta:
        if self.time_until is not None:
            return self.time_until - self.time_since
        else:
            return datetime.datetime.now(tz=datetime.timezone.utc) - self.time_since

    def __str__(self):
        running=", still running" if self.time_until is None else ""
        duration = format_timedelta(self.clock_duration())

        return f"Clock entry (ID {self.id}) // {duration}{running}"

    def stop(self):
        self._api.stop_clock(self)
        return self._api.get_entry(self.id)

    def start(self):
        return self._api.start_clock(self)

class LumpSumValue(FromJsonBlob, BaseEntry):
    def __init__(self, api, customer, service,
                 time_since, lumpsum,
                 text=None, user=None,
                 project=None, billable=False):
        self.type = 2
        self.text = text
        self._api = api
        self.customers_id = customer.id
        self.services_id = service.id
        self.projects_id = project.id if project is not None else None
        self.billable = billable
        self.time_since = time_since
        self.lumpsum = lumpsum
        self.users_id = user.id

    def __str__(self):
        return f"Lump sum entry (ID {self.id}) // {self.lumpsum:.02f} EUR"

class EntryWithLumpSumService(FromJsonBlob, BaseEntry):
    pass

class EntryApi(ClockodoApi):
    def get_entry(self, id):
        response = self._api_call(f"v2/entries/{id}")
        return BaseEntry.from_json_blob(self, response["entry"])

    def edit_entry(self, entry: BaseEntry, edit: dict):
        for term in ["customer", "service", "project", "user"]:
            if term in edit:
                edit[term + "s_id"] = edit[term].id if edit[term] is not None else None
                del edit[term]
        for term in ["time_since", "time_until"]:
            if term in edit and isinstance(edit[term], datetime.datetime):
                edit[term] = iso8601(edit[term])

        response = self._api_call(f"v2/entries/{entry.id}", method="PUT", params=edit)

        return BaseEntry.from_json_blob(self, response["entry"])

    def list_entries(self, time_since: datetime.datetime,
                     time_until: datetime.datetime,
                     page=None,
                     filters={},
                     revenues_for_hard_budget=False):
        time_since = iso8601(time_since)
        time_until = iso8601(time_until)

        data = {
            "time_since": time_since,
            "time_until": time_until,
            "page": page,
            # it's not me who invented this kinda long field! ~Vika
            "calc_also_revenues_for_projects_with_hard_budget": str(int(revenues_for_hard_budget))
        }
        for k, v in filters.items():
            if k in ["customer", "project", "service"]:
                data[f"filters[{k}s_id]"] = v.id
            else:
                if isinstance(v, bool):
                    v = str(int(v))
                data[f"filters[{k}]"] = v

        result = self._api_call("v2/entries", params=data)
        result["entries"] = list(map(lambda e: BaseEntry.from_json_blob(self, e), result["entries"]))

        return result

    def iter_entries(self, time_since: datetime.datetime,
                     time_until: datetime.datetime,
                     filters={},
                     revenues_for_hard_budget=False):
        time_since = iso8601(time_since)
        time_until = iso8601(time_until)

        params = {
            "time_since": time_since,
            "time_until": time_until,
            "page": 1,
            # it's not me who invented this kinda long field! ~Vika
            "calc_also_revenues_for_projects_with_hard_budget": str(int(revenues_for_hard_budget))
        }
        for k, v in filters.items():
            if k in ["customer", "project", "service"]:
                params[f"filters[{k}s_id]"] = v.id
            else:
                if isinstance(v, bool):
                    v = str(int(v))
                params[f"filters[{k}]"] = v

        count_pages = None
        while count_pages is None or params["page"] <= count_pages:
            response = self._api_call(f"v2/entries", params=params)
            yield from map(lambda e: BaseEntry.from_json_blob(self, e), response["entries"])

            if "paging" not in response:
                break
            if count_pages is None:
                count_pages = response["paging"]["count_pages"]
            params["page"] = response["paging"]["current_page"] + 1
