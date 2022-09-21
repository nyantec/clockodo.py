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
$ clockodo
ID XXXXXXXX, since since 2022-09-21T13:02:36Z, still running
Customer: nyantec (customer ID XXXXXX)
Service: Software Development (service ID XXXXXX)
Description: Developing a CLI for clocko:do
```

#### Stop current clock
```console
$ clockodo stop
Clock stopped.
```

### From Python
```python
import clockodo
import clockodo.clock

api = Clockodo(api_user, api_token)

clock = api.current_clock()

customer = clock.customer()
project = clock.project()
service = clock.service()

print("Customer:", str(customer))
print("Project:", str(project))
print("Service:", str(service))
print(clock.text)

new_clock = clockodo.clock.ClockEntry(
    api,
    customer=customer, project=None,
    service=service,
    text="Lorem ipsum dolor sit amet"
)

api.start_clock(new_clock)
```
