{
  description = "CLI and Python API for clocko:do";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

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
    in poetry-env.env.overrideAttrs (old: {
      nativeBuildInputs = (old.nativeBuildInputs or []) ++ (with pkgs; [
        poetry
      ]);
    });
  }));
}
