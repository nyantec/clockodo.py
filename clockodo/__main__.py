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
import clockodo

def eprint(*args, **kwargs):
    return print(*args, file=sys.stderr, **kwargs)

def list_pages(api_call, key):
    count_pages = None
    current_page = None

    while count_pages is None or current_page != count_pages:
        response = api_call(None if current_page == None else current_page + 1)

        for c in response[key]:
            print(str(c))

        if count_pages is None:
            count_pages = response["paging"]["count_pages"]
        current_page = response["paging"]["current_page"]

def main():
    try:
        api_user = os.getenv("CLOCKODO_API_USER")
        api_token = os.getenv("CLOCKODO_API_TOKEN")
        if api_user is None or api_token is None:
            eprint("CLOCKODO_API_USER should contain your user email, CLOCKODO_API_TOKEN should contain your access token.")
            sys.exit(1)

        args = sys.argv[1:]
        api = clockodo.Clockodo(api_user=api_user, api_token=api_token)

        if len(args) == 0 or (len(args) == 1 and args[0] == "clock"):
            print("Current clock:")
            clock = api.current_clock()
            customer = clock.customer()
            project = clock.project()
            service = clock.service()
            print("ID {clock.id}, since {clock.time_since}, {until}".format(
                clock=clock,
                until="still running" if clock.time_until is None else f"until {clock.time_until}"
            ))
            print("Customer:", str(customer))

            if project is not None:
                print("Project:", str(project))

            print("Service", str(service))
            print("Description:", clock.text())
        elif len(args) > 1 and args[0] == "clock":
            if args[1] == "stop":
                api.stop_clock(api.current_clock())
                print("Clock stopped.")
        elif args[0] == "customer":
            if len(args) == 1:
                list_pages(lambda p: api.list_customers(page=p), "customers")
        elif args[0] == "project":
            if len(args) == 1 or (len(args) > 1 and args[1] == "list"):
                customer = None
                if len(args) == 4 and args[2] == "--customer":
                    customer = api.get_customer(int(args[3]))
                list_pages(lambda p: api.list_projects(page=p, customer=customer), "projects")
        elif args[0] == "service":
            for s in api.list_services()["services"]:
                print(str(s))


    except clockodo.api.ClockodoApiError as e:
        if e.status == 401:
            eprint("clocko:do API returned HTTP 401.")
            eprint("Ensure you have CLOCKODO_API_USER and CLOCKODO_API_TOKEN environment variables set properly.")
        else:
            eprint("clocko:do API returned HTTP {}: {}".format(e.status, e.data["error"]["message"]))
        sys.exit(1)
if __name__ == "__main__":
    main()
