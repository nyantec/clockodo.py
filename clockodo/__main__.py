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

import os
import sys
import datetime
import click
import clockodo

Iso8601 = click.DateTime([clockodo.entry.ISO8601_TIME_FORMAT])

# https://stackoverflow.com/questions/52053491/a-command-without-name-in-click/52069546#52069546
class DefaultCommandGroup(click.Group):
    """Create a group which can run a default command if no other commands match."""

    def command(self, *args, **kwargs):
        default_command = kwargs.pop('default_command', False)
        if default_command and not args:
            kwargs['name'] = kwargs.get('name', '<>')
        decorator = super(DefaultCommandGroup, self).command(*args, **kwargs)

        if default_command:
            def new_decorator(f):
                cmd = decorator(f)
                self.default_command = cmd.name
                return cmd

            return new_decorator

        return decorator

    def resolve_command(self, ctx, args):
        try:
            # test if the command parses
            return super(
                DefaultCommandGroup, self).resolve_command(ctx, args)
        except click.UsageError:
            # command did not parse, assume it is the default command
            args.insert(0, self.default_command)
            return super(
                DefaultCommandGroup, self).resolve_command(ctx, args)


def eprint(*args, **kwargs):
    return print(*args, file=sys.stderr, **kwargs)


def our_tz():
    return datetime.datetime.now(tz=datetime.timezone.utc).astimezone().tzinfo


def clock_entry_cb(clock):
    customer = str(clock.customer())
    project = ""
    _project = clock.project()
    if _project is not None:
        _project = str(_project)
        project = f"\nProject: {project}"
    service = str(clock.service())
    time_since = datetime.datetime.strftime(
        clock.time_since.astimezone(our_tz()),
        clockodo.entry.ISO8601_TIME_FORMAT
    )
    if clock.time_until is None:
        time_until = ""
    else:
        time_until = "\nEnded at: " + datetime.datetime.strftime(
            clock.time_until.astimezone(our_tz()),
            clockodo.entry.ISO8601_TIME_FORMAT
        )
    return f"""---
{clock}
Started at: {time_since}{time_until}
Customer: {customer}{project}
Service: {service}
Description: {clock.text}
---"""


def list_pages(api_call, key, cb=str):
    count_pages = None
    current_page = None

    while count_pages is None or current_page != count_pages:
        response = api_call(None if current_page == None else current_page + 1)

        for c in response[key]:
            print(cb(c))
        if "paging" not in response:
            break
        if count_pages is None:
            count_pages = response["paging"]["count_pages"]
        current_page = response["paging"]["current_page"]

@click.group()
@click.option('--user', envvar='CLOCKODO_API_USER', show_envvar=True)
@click.option('--token', envvar='CLOCKODO_API_TOKEN', show_envvar=True)
@click.pass_context
def cli(ctx, user, token):
    ctx.obj = clockodo.Clockodo(user, token)

@cli.group(cls=DefaultCommandGroup, invoke_without_command=True)
@click.pass_context
def clock(ctx):
    if not ctx.invoked_subcommand:
        ctx.invoke(current_clock)

@clock.command(default_command=True, name="current")
@click.pass_obj
def current_clock(api):
    clock = api.current_clock()
    if clock is None:
        print("No running clock")
        sys.exit(1)
    print(clock_entry_cb(clock))

@clock.command(name="stop")
@click.pass_obj
def stop_clock(api):
    clock = api.current_clock().stop()
    print("Finished:", str(clock))


@clock.command(name="new")
@click.option("--customer", type=int)
@click.option("--project", type=int, required=False)
@click.option("--service", type=int)
@click.option("--billable", type=bool, required=False)
@click.argument("text", type=str)
@click.pass_obj
def new_clock(api, customer, project, service, text, billable):
    customer = api.get_customer(customer)
    project = api.get_project(project) if project is not None else None
    service = api.get_service(service)
    clock = clockodo.clock.ClockEntry(
        api=api,
        customer=customer,
        project=project,
        service=service,
        text=text,
        billable=billable
    ).start()
    print(clock_entry_cb(clock))


@clock.command(name="edit")
@click.option("--customer", type=int, required=False)
@click.option("--project", type=int, required=False)
@click.option("--service", type=int, required=False)
@click.option("--text", type=str, required=False)
@click.option("--time-since", type=Iso8601, required=False)
@click.option("--billable", type=bool, required=False)
@click.pass_obj
def edit_clock(api, **kwargs):
    clock = api.current_clock()
    print(clock_entry_cb(clock.edit(kwargs)))


@cli.command()
@click.option('--active', required=False, default=None, type=bool)
@click.pass_obj
def customers(api, active=None):
    list_pages(lambda p: api.list_customers(page=p, active=active), "customers")

@cli.command()
@click.option('--active', required=False, default=None, type=bool)
@click.option('--customer', required=False, default=None, type=int)
@click.pass_obj
def projects(api, active, customer):
    if customer is not None:
        customer = api.get_customer(customer)
    list_pages(lambda p: api.list_projects(page=p, customer=customer, active=active), "projects")

@cli.command()
@click.pass_obj
def services(api):
    list_pages(lambda p: api.list_services(page=p), "services")


@cli.command()
@click.argument('time_since', type=Iso8601, required=False)
@click.argument('time_until', type=Iso8601, required=False)
@click.pass_obj
def entries(api, time_since, time_until):
    if time_since is None:
        time_since = datetime.datetime.combine(
            datetime.date.today(),
            datetime.time(0, tzinfo=our_tz())
        )
    if time_until is None:
        time_until = datetime.datetime.combine(
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.time(0, tzinfo=our_tz())
        )

    count_pages = None
    current_page = None
    entries = []
    while count_pages is None or current_page != count_pages:
        response = api.list_entries(
            page=None if current_page is None else current_page + 1,
            time_since=time_since, time_until=time_until
        )

        entries.extend(response["entries"])
        if "paging" not in response:
            break
        if count_pages is None:
            count_pages = response["paging"]["count_pages"]
        current_page = response["paging"]["current_page"]

    break_count = 0
    total_break_duration = datetime.timedelta(0)
    total_work_time = datetime.timedelta(0)

    for i, entry in enumerate(entries):
        print(clock_entry_cb(entry))
        if entry.duration is not None:
            total_work_time += datetime.timedelta(seconds=entry.duration)
        else:
            total_work_time += datetime.datetime.now(tz=datetime.timezone.utc) - entry.time_since

        if entry.time_until is not None:
            try:
                next_since = entries[i+1].time_since
            except IndexError:
                next_since = datetime.datetime.now(tz=our_tz())
            break_duration = next_since - entry.time_until
            total_break_duration += break_duration
            if break_duration > datetime.timedelta(0):
                print("Break:", clockodo.entry.format_timedelta(break_duration))
                break_count += 1

    print("Total work time:", clockodo.entry.format_timedelta(total_work_time))
    print(f"Breaks: {break_count}, total duration:", clockodo.entry.format_timedelta(total_break_duration))
if __name__ == "__main__":
    cli()
