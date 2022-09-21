{
  description = "CLI and Python API for clocko:do";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  # XXX https://github.com/nix-community/poetry2nix/pull/713
  inputs.poetry2nix.url = "github:farcaller/poetry2nix/patch-1";

  outputs = { self, nixpkgs, flake-utils, poetry2nix }: {
    overlay = nixpkgs.lib.composeManyExtensions [
      poetry2nix.overlay
      (final: prev: {
        clockodo-py = final.poetry2nix.mkPoetryApplication {
          projectDir = ./.;

          meta = {
            mainProgram = "clockodo";
          };
        };
      })
    ];
  } // (flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system;
      overlays = [ self.overlay ];
    };
  in {
    packages = {
      clockodo-py = pkgs.clockodo-py;
      default = pkgs.clockodo-py;
    };
    devShells.default = let
      poetry-env = pkgs.poetry2nix.mkPoetryEnv {
        projectDir = ./.;
        editablePackageSources = {
          clockodo = ./.;
        };
      };
    in pkgs.mkShell {
      buildInputs = [ poetry-env ];
    };
  }));
}
