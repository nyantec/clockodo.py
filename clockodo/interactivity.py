import datetime
import functools
import clockodo
import inquirer

def our_tz():
    return datetime.datetime.now(tz=datetime.timezone.utc).astimezone().tzinfo


def inject_api(fun, api):
    @functools.wraps(fun)
    def _inner(*args, **kwargs):
        return fun(*args, **kwargs, api=api)

    return _inner


def memoize_once(fun):
    _cached = None
    @functools.wraps(fun)
    def _inner(*args, **kwargs):
        nonlocal _cached
        if _cached is None:
            _cached = fun(*args, **kwargs)
        return _cached

    return _inner


@memoize_once
def project_entries(answers, api=None):
    return [("(none)", None)] \
        + [(p.name, p) for p in api.iter_projects(
            active=True,
            customer=answers["customer"]
        )]


@memoize_once
def customer_entries(answers, api=None):
    return [(c.name, c) for c in api.iter_customers(active=True)]


@memoize_once
def service_entries(answers, api=None):
    return [(s.name, s) for s in filter(lambda s: s.active, api.iter_services())]


def validate_timestamp(answers, current):
    try:
        current = datetime.datetime.strptime(current, "%H:%M:%S").time()
    except ValueError:
        raise inquirer.errors.ValidationError(current, reason="Time doesn't match format")
    time_since = answers.get("time_since", None)
    if time_since is not None:
        time_since = datetime.datetime.strptime(time_since, "%H:%M:%S").time()
        if current < time_since:
            raise inquirer.errors.ValidationError(current, reason="End time is before start time")
    return current


@memoize_once
def get_last_clock_out_time(api=None):
    # Figure out today's timespan
    time_since = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(0, tzinfo=our_tz())
    )
    time_until = datetime.datetime.combine(
        datetime.date.today() + datetime.timedelta(days=1),
        datetime.time(0, tzinfo=our_tz())
    )

    # Get the last clock entry for this period
    *_, last = api.iter_entries(time_since, time_until)

    if isinstance(last, clockodo.entry.ClockEntry) and last.time_until is not None:
        return last.time_until.astimezone(our_tz()).strftime("%H:%M:%S")
