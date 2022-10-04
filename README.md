# clocko:do for Python (unofficial)
## Installation
### Using Nix
```console
$ nix profile install github:nyantec/clockodo.py
```

Or use as an input in your own flake:

```nix
{
  inputs.nixpkgs = "github:nixos/nixpkgs/nixos-unstable";
  inputs.clockodo-py = "github:nyantec/clockodo.py";

  outputs = { self, nixpkgs, clockodo }: {
    nixosConfigurations.example = nixpkgs.lib.nixosSystem {
      modules = [
        ./configuration.nix
        ({ config, pkgs, lib, ... }: {
          nixpkgs.overlays = [ clockodo.overlay ];
          environment.systemPackages = [
            clockodo-py
          ];
        })
      ];
    };
  };
}
```

## Usage
### From CLI
This application requires the following environment variables:
 - `CLOCKODO_API_USER` set to the email address you use to log into clocko:do 
 - `CLOCKODO_API_TOKEN` set to a token you can receive in the clocko:do dashboard

#### Show current clock
```console
$ clockodo clock
---
Clock entry (ID XXXXXXXX) // 0h12m, still running
Started at: 2022-09-21T15:02:36+0300
Customer: nyantec (customer ID XXXXXX)
Service: Software Development (service ID XXXXXX)
Description: Developing a CLI for clocko:do
---
```

#### Stop current clock
```console
$ clockodo clock stop
Clock stopped.
```

#### Start new clock (also works to switch to a new tasks)
```console
$ clockodo clock new \
    --customer XXXXXX \
    --service XXXXXX \
    "Description for your clock entry. --project XXXXX can optionally be included"
    --billable true
```

You can use names for customers, projects and services -- an exact match will be used.

Alternatively, use `--XXX-id` forms with IDs that are shown when listing customers, projects or services.

#### Edit currently running clock
```console
$ clockodo clock edit [PARAMETERS]
```

You can edit the following things:
 - Customer (`--customer <name>` or `--customer-id XXXXXX`)
 - Project (`--project <name>` or `--project-id XXXXXX`)
 - Service (`--service <name>` or `--service-id XXXXXX`)
 - Description (`--text "blablabla"`)
 - Starting time (`--time-since %Y-%m-%dT%H:%M:%S%z`)
 - Billability (`--billable <true|false>`)

#### List customers, projects and services
```console
$ clockodo customers [--active <true|false>]
```

```console
$ clockodo projects [--active <true|false>] [--customer-id XXXXXX|--customer name]
```

```console
$ clockodo services
```

#### List your clock entries
The default period is to get all of one's entries for today.

```console
$ clockodo entries
---
Clock entry (ID XXXXXXXX) // 1h58m
Started at: 2022-09-27T13:47:00+0300
Ended at: 2022-09-27T15:45:00+0300
Customer: nyantec (customer ID XXXXXX)
Service: Business Administration (service ID XXXXXX)
Description: Monthly review
---
Break: 1h0m
---
Clock entry (ID XXXXXXXX) // 0h22m, still running
Started at: 2022-09-27T16:45:00+0300
Customer: nyantec (customer ID XXXXXX)
Service: Project Engineering (service ID XXXXXX)
Description: Documenting clockodo.py
---
Total work time: 2h20m
Breaks: 1, total duration: 1h0m
```

### From Python
```python
import clockodo

api = Clockodo(api_user, api_token)
clock = api.current_clock()

customer = clock.customer()
project = clock.project()
service = clock.service()

print("Customer:", str(customer))
print("Project:", str(project))
print("Service:", str(service))
print(clock.text)

clock = clockodo.clock.ClockEntry(
    api,
    customer=customer, project=None,
    service=service,
    text="Lorem ipsum dolor sit amet"
).start()

# Do some work...

finished_entry = clock.stop()
```
