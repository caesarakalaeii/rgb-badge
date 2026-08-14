{
  # Keep this line accurate and one line long: `nix flake metadata` prints it,
  # and it is the first thing a cold agent learns about the repo.
  description = "rgb-badge -- 2560-LED ESP32-S3 matrix badge: KiCad board automation, ESP32 firmware, video-to-frame tooling. Run `nix flake show` for the command map.";

  # nixpkgs is the only input, on purpose.
  #
  # flake-utils would buy exactly one thing here -- eachDefaultSystem -- which is
  # the three-line genAttrs below. In exchange it costs a second lock node in
  # every repo (flake-utils transitively pulls `systems`, so really two), a
  # second upstream that can break one repo and not the others, and a hardcoded
  # system list this repo cannot edit. That list is currently broken: it still
  # contains x86_64-darwin, which now throws (see `systems` below).
  #
  # nixos-unstable is the same channel the author's own NixOS config tracks, so
  # `nix develop` here and `nixos-rebuild` there resolve the same store paths and
  # share one cache.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    # `...` rather than a closed { self, nixpkgs }: adding a second input later
    # would otherwise fail with "called with unexpected argument 'self'".
    { nixpkgs, ... }:
    let
      lib = nixpkgs.lib;

      # x86_64-darwin is deliberately absent. nixpkgs 26.11 replaced that whole
      # attribute set with `throw "Nixpkgs 26.11 has dropped support for
      # x86_64-darwin"`. genAttrs is lazy, so plain `nix develop` on Linux would
      # not notice -- it detonates later, on `nix flake check --all-systems`.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      # Stand-in for flake-utils.lib.eachDefaultSystem. Passes `pkgs` rather than
      # a system string, because that is what every call site below wants.
      forAllSystems = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      # ======================================================================
      # PER-REPO BLOCK 0 -- the one Python, and where KiCad hides pcbnew
      # ======================================================================
      # 20 of this repo's 22 Python files begin with `import pcbnew`. pcbnew is
      # NOT on PyPI and never will be -- it is a SWIG binding shipped inside
      # KiCad as `_pcbnew.so`, a CPython extension module compiled against one
      # specific interpreter ABI. So the interpreter here is not a free choice:
      # it must be the same major.minor that kicad-base was built against, which
      # on this pin is 3.14 (kicad 10.0.5 carries a python3-3.14.7-env). Pinning
      # `python313` here would leave every script in cad/ and scripts/ dead with
      # `ModuleNotFoundError: No module named pcbnew`, and pinning rolling
      # `python3` would break it silently on some future nixpkgs bump.
      #
      # `checks.pcbnew` below actually imports the module, so if a nixpkgs bump
      # moves KiCad onto 3.15 this drift fails at the flake gate rather than
      # halfway through an agent's task.
      python = pkgs: pkgs.python314;

      # Every third-party import in the repo exists in nixpkgs, so the shell
      # works OFFLINE and there is deliberately no venv and no `setup` verb for
      # Python. Do not "fix" this by adding uv + requirements.txt: that would
      # reintroduce a network bootstrap for packages nixpkgs already has, and a
      # second interpreter that cannot see pcbnew.
      #
      # test_animations/requirements.txt maps to these exactly:
      #   opencv-python -> opencv4   numpy -> numpy   pillow -> pillow
      #   requests -> requests       tqdm  -> tqdm
      pythonEnv =
        pkgs:
        (python pkgs).withPackages (ps: [
          ps.opencv4
          ps.numpy
          ps.pillow
          ps.requests
          ps.tqdm
        ]);

      # `${kicad.base}/lib/python3.14/site-packages`, spelled so the version
      # comes from the interpreter rather than being hardcoded twice. Exported as
      # PYTHONPATH in envVars, which is what makes `import pcbnew` work from the
      # plain interpreter -- the scripts in cad/ are standalone CLIs
      # (`pcbnew.LoadBoard(path)`), not just GUI console snippets.
      pcbnewPath = pkgs: "${pkgs.kicad-small.base}/${(python pkgs).sitePackages}";

      # ======================================================================
      # PER-REPO BLOCK 1 -- the toolchain
      # ======================================================================
      # Everything the commands below need. `nix flake check` realises this
      # closure, so a typo'd attr name fails at the flake gate instead of
      # surfacing as "command not found" halfway through a task.
      #
      # Explicit `pkgs.foo`, never `with pkgs; [ ... ]`: when an attr disappears
      # in a nixpkgs bump, `with` reports a bare undefined identifier with no
      # hint of which set it came from, and the name is not greppable.
      toolchain =
        pkgs:
        [
          (pythonEnv pkgs)

          # cad/freerouting_io.py exists purely to round-trip a board through
          # Freerouting (ExportSpecctraDSN -> route -> ImportSpecctraSES). Its
          # docstring tells you to download freerouting.jar yourself and run
          # `java -jar`; nixpkgs ships it with its own JRE, so the middle step is
          # just `freerouting` on PATH and needs no download.
          pkgs.freerouting

          # ---- ESP32 firmware: four platformio.ini projects under
          # test_animations/ (root, bad_apple/, bims/, cat/), all
          # espressif32 + arduino + FastLED ----
          pkgs.platformio
          pkgs.esptool

          # ---- video -> LED frame conversion (test_animations/) ----
          # bad_apple_converter.py shells out to yt-dlp, and fix_video_codec.sh
          # exits early with an install hint unless ffmpeg is on PATH.
          # ffmpeg-headless rather than ffmpeg: same CLI, much smaller closure,
          # and nothing here needs the GUI/SDL outputs.
          pkgs.ffmpeg-headless
          pkgs.yt-dlp

          # ---- linters for the two languages that actually have source here ----
          pkgs.ruff
          pkgs.shellcheck
          pkgs.shfmt

          # ---- present in every repo in the fleet ----
          pkgs.git
          pkgs.jq
          pkgs.gnumake
          # GNU xargs specifically, for `xargs -0 -r` in lint/fmt below: BSD
          # xargs on darwin has no -r and would run the linter with no files.
          pkgs.findutils
        ]
        ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
          # ---- KiCad: the whole reason this repo has a Python toolchain ----
          #
          # Linux-only, and NOT by choice: on the locked nixpkgs, kicad-base sets
          # `broken = true` for aarch64-darwin, so merely evaluating its outPath
          # there fails with "Refusing to evaluate package 'kicad-base-10.0.5'
          # ... because it has problems: - broken". Note the trap: `nix eval
          # nixpkgs#legacyPackages.aarch64-darwin.kicad-small.base.name` answers
          # happily, because `.name` never forces the derivation -- this only
          # surfaces on `nix flake check --all-systems`. Gate on
          # `stdenv.hostPlatform.isLinux`, never on attribute presence.
          #
          # The cost of the darwin gap is that `dev-test` (and anything else
          # importing pcbnew) does not work on an Apple Silicon mac. Everything
          # else in this flake -- firmware, converter, linters -- does.
          #
          # kicad-small, NOT kicad: the difference is the bundled
          # symbol/footprint libraries, which this repo does not need from
          # nixpkgs. The board files embed their own footprint definitions
          # (verified: pcbnew.LoadBoard on cad/led_bage.kicad_pcb yields 3254
          # footprints with no library set up), no script in scripts/ or cad/
          # loads a footprint from a library, and kicad-repos.txt shows the
          # maintainer cloning the KiCad libraries from GitLab by hand anyway.
          # This is still a ~2.7 GB closure and by far the heaviest thing here --
          # deliberately over the usual budget, because pcbnew is not optional
          # for 20 of the 22 Python files in this repo. Do not "upgrade" this to
          # `pkgs.kicad`; that adds multiple GB of libraries nothing here reads.
          pkgs.kicad-small
        ];

      # ======================================================================
      # PER-REPO BLOCK 2 -- libraries that get dlopened, not linked
      # ======================================================================
      # Everything in `toolchain` above is properly linked by nix, so this list
      # is not what makes cv2 or pcbnew import -- those work without it. It is
      # load-bearing for the repo's OWN documented escape hatch:
      # test_animations/convert_with_venv.sh and bad_apple/setup_and_flash.sh
      # both build a .venv and `pip install opencv-python`, which is a manylinux
      # wheel whose .so files are dlopened. Without libstdc++ on the search path
      # that fails with `libstdc++.so.6: cannot open shared object file`.
      #
      # This fixes shared libraries only. A prebuilt *executable* -- notably the
      # xtensa toolchain PlatformIO downloads -- still needs a real ELF
      # interpreter at `/lib64/ld-linux-x86-64.so.2`, which no project flake can
      # supply (stock NixOS ships a stub there that exits 127 unless
      # `environment.ldso` or `programs.nix-ld.enable` is set). `pio` sidesteps
      # this by being an FHS bwrap wrapper; do not let that convince you this
      # shell is self-contained.
      nativeLibs = pkgs: [
        pkgs.stdenv.cc.cc.lib
        pkgs.zlib
      ];

      # ======================================================================
      # PER-REPO BLOCK 3 -- constant environment variables
      # ======================================================================
      # Only values that are constants belong here. Anything that must READ an
      # existing value (LD_LIBRARY_PATH), UNSET something (SOURCE_DATE_EPOCH) or
      # touch the work tree (PLATFORMIO_CORE_DIR) goes in envPreamble below.
      #
      # This attrset is applied to BOTH surfaces -- the dev shell and every
      # `nix run` wrapper -- so a command cannot behave differently depending on
      # how it was invoked.
      envVars =
        pkgs:
        lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
          # The single most load-bearing line in this file: it is what turns the
          # stock interpreter into one that can `import pcbnew`. Safe to set
          # globally because this shell ships exactly one Python, so there is no
          # second interpreter for it to leak into.
          #
          # Guarded by isLinux for the same reason kicad-small is: interpolating
          # `kicad-small.base` into a string forces that derivation, and it is
          # marked broken on aarch64-darwin. An unguarded PYTHONPATH here would
          # break `nix flake check --all-systems` even though nothing on darwin
          # ever reads it.
          PYTHONPATH = pcbnewPath pkgs;
        }
        // {
          # Progress bars are redrawn per frame and there is no tty under
          # `nix run`, so without this an agent captures a screenful of ANSI
          # noise per download.
          PLATFORMIO_DISABLE_PROGRESSBAR = "true";

          # The scripts are run ad hoc (`python3 cad/normalize_led_rotation.py`),
          # so bytecode caching buys nothing and only litters the work tree with
          # __pycache__ next to the board files.
          PYTHONDONTWRITEBYTECODE = "1";
        };

      # ======================================================================
      # PER-REPO BLOCK 3b -- env that needs $REPO_ROOT, so it cannot be a constant
      # ======================================================================
      # This is injected into the dev shell's hook AND into every `nix run`
      # wrapper, immediately after $REPO_ROOT is anchored. Both surfaces on
      # purpose: if it lived only in shellHook (which is how the plain house
      # template would express it) then `nix run .#build` would quietly dump
      # PlatformIO's downloads into $HOME while `dev-build` used the work tree --
      # the same command with two different states, which is exactly the class of
      # bug the shared-wrapper design exists to prevent.
      envPreamble = ''
        # PlatformIO downloads ~1 GB of xtensa toolchain and framework packages
        # on first build. Anchoring it in the work tree keeps a reset to one
        # `rm -rf .platformio` instead of hunting through $HOME, and keeps two
        # checkouts from fighting over one cache. The var survives into pio's FHS
        # sandbox.
        export PLATFORMIO_CORE_DIR="$REPO_ROOT/.platformio"
      '';

      # ======================================================================
      # PER-REPO BLOCK 4 -- the command map
      # ======================================================================
      # THE single source of truth. It generates `apps` (so `nix run .#test`
      # works), the `dev-*` wrappers on PATH inside the shell, and `dev-help`.
      # Nothing is written twice, so `nix flake show` can never disagree with
      # what `dev-test` actually runs.
      #
      # Note what is ABSENT: there is no Python `setup`, because every Python
      # dependency comes from nixpkgs and the shell therefore works offline.
      # `setup` here is PlatformIO-only.
      #
      # The verbs deliberately mirror test_animations/Makefile, which already
      # defines setup/build/flash/monitor for this repo -- `run` is its `flash`.
      #
      # `text` is bash under `set -euo pipefail`, shellcheck'd at BUILD time, and
      # it runs in the caller's current directory. That last part matters more
      # here than in most repos: there are FOUR platformio.ini projects, so the
      # pio verbs act on whichever one you have cd'd into.
      commands = pkgs: {
        setup = {
          description = "(network) install PlatformIO packages for the firmware project in the current directory";
          text = ''
            if [ ! -f platformio.ini ]; then
              echo "no platformio.ini here -- cd into test_animations/, test_animations/bad_apple/, test_animations/bims/ or test_animations/cat/ first" >&2
              exit 1
            fi
            pio pkg install "$@"
          '';
        };
        build = {
          description = "compile the ESP32 firmware in the current directory (first run needs network)";
          text = ''
            if [ ! -f platformio.ini ]; then
              echo "no platformio.ini here -- cd into a firmware project under test_animations/ first" >&2
              exit 1
            fi
            pio run "$@"
          '';
        };
        test = {
          # The closest thing this repo has to a test suite: there is no pytest
          # and scripts/test_led_rotations.py only runs inside KiCad's GUI
          # console. Parsing every board through pcbnew is a real check -- it
          # catches a corrupted .kicad_pcb and it proves the KiCad/Python ABI
          # pairing is intact on the machine you are standing on.
          #
          # A bare `python3` is correct here and resolves identically on both
          # surfaces, because this repo has no .venv for the wrappers' PATH
          # prepend to shadow.
          description = "parse every tracked .kicad_pcb through pcbnew (args: specific boards)";
          text = ''
            python3 -c '
            import os, subprocess, sys
            import pcbnew

            paths = sys.argv[1:]
            if not paths:
                os.chdir(os.environ.get("REPO_ROOT", "."))
                paths = subprocess.run(
                    ["git", "ls-files", "*.kicad_pcb"],
                    capture_output=True, text=True, check=True,
                ).stdout.split()
            if not paths:
                sys.exit("no .kicad_pcb files found")

            print("pcbnew", pcbnew.GetBuildVersion())
            for p in paths:
                board = pcbnew.LoadBoard(p)
                print(
                    "ok", p,
                    len(list(board.GetFootprints())), "footprints,",
                    len(list(board.GetTracks())), "tracks",
                )
            print("parsed", len(paths), "board(s)")
            ' "$@"
          '';
        };
        lint = {
          # Both linters run before we exit, rather than fail-fast, so one call
          # reports the whole picture instead of hiding ruff behind shellcheck.
          #
          # Be warned: this repo is NOT lint-clean today. On the locked toolchain
          # a fresh checkout reports 122 ruff findings and 22 shellcheck
          # findings, so `dev-lint` exits 1 before you have changed anything.
          # That is pre-existing, not something this flake introduced, and it is
          # left visible on purpose. Do NOT silence it by adding a permissive
          # ruff config or a --severity floor -- fix the findings, or accept the
          # noise and diff it against a baseline.
          description = "ruff check + shellcheck over tracked shell scripts (repo is not clean today)";
          text = ''
            status=0
            git -C "$REPO_ROOT" ls-files -z "*.sh" | xargs -0 -r shellcheck || status=1
            ruff check "$@" || status=1
            exit "$status"
          '';
        };
        fmt = {
          description = "shfmt -w on tracked shell scripts + ruff format (rewrites files)";
          text = ''
            git -C "$REPO_ROOT" ls-files -z "*.sh" | xargs -0 -r shfmt -w
            ruff format "$@"
          '';
        };
        run = {
          # test_animations/Makefile calls this `flash`; the house vocabulary
          # calls it `run`. Needs the badge plugged in, the user in `dialout`,
          # and udev rules from pkgs.platformio-core.udev in the host NixOS
          # config -- none of which a project flake can provide.
          description = "flash the firmware in the current directory to a connected ESP32 (needs USB)";
          text = ''
            if [ ! -f platformio.ini ]; then
              echo "no platformio.ini here -- cd into a firmware project under test_animations/ first" >&2
              exit 1
            fi
            pio run --target upload "$@"
          '';
        };
      };

      # ======================================================================
      # GENERIC MACHINERY -- shared across the fleet, do not edit
      # ======================================================================

      # Prepend, never assign: a host LD_LIBRARY_PATH may be carrying something
      # the user needs, and clobbering it breaks binaries they launch from here.
      # Linux only -- on darwin the loader variable is DYLD_*, and exporting a
      # Linux-shaped value there is at best useless.
      ldPreamble =
        pkgs:
        lib.optionalString (pkgs.stdenv.hostPlatform.isLinux && nativeLibs pkgs != [ ]) ''
          export LD_LIBRARY_PATH="${lib.makeLibraryPath (nativeLibs pkgs)}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        '';

      # Every command gets $REPO_ROOT. `nix run` and `nix develop` both start in
      # whatever directory they were invoked from, so a bare `.platformio`
      # silently forks a second environment as soon as an agent works from a
      # subdirectory -- and with four platformio.ini projects in this repo, that
      # is the normal case rather than the exception. Note we do NOT cd there:
      # commands act on the caller's cwd on purpose.
      rootPreamble = ''
        REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
        export REPO_ROOT
      '';

      # One derivation per command, reused by both `apps` and the dev shell, so
      # the two can never diverge. `dev-` prefixed because a bare `test` binary
      # earlier on PATH would shadow the POSIX shell builtin and quietly break
      # every script in the repo that uses it.
      wrappers =
        pkgs:
        lib.mapAttrs (
          name: cmd:
          pkgs.writeShellApplication {
            name = "dev-${name}";
            runtimeInputs = toolchain pkgs;
            runtimeEnv = envVars pkgs;
            meta.description = cmd.description;
            text = ''
              ${rootPreamble}
              ${ldPreamble pkgs}
              ${envPreamble}
              ${cmd.text}
            '';
          }
        ) (commands pkgs);

      helpFor =
        pkgs:
        let
          cmds = commands pkgs;
          names = lib.attrNames cmds;
          width = lib.foldl' (a: n: lib.max a (builtins.stringLength n)) 0 names;
          pad = n: n + lib.concatStrings (lib.genList (_: " ") (width - builtins.stringLength n));
          line = n: c: "  dev-${pad n}  ${c.description}";
        in
        pkgs.writeShellApplication {
          name = "dev-help";
          meta.description = "print this repo's command map (works offline)";
          text = ''
            cat <<'EOF'
            ${lib.concatStringsSep "\n" (lib.mapAttrsToList line cmds)}
            EOF
          '';
        };
    in
    {
      # `nix flake show` -- the discovery entrypoint, and deliberately the whole
      # machine-facing contract: every app carries a meta.description, which
      # `nix flake show` prints inline and `nix flake show --json` exposes at
      # .apps.<system>.<name>.description. Pure evaluation, so an agent gets the
      # entire command map in one cheap call without reading a README.
      #
      # Do NOT invent a top-level output for this (`agentManifest`, `probeThing`
      # ...). Nix answers with `warning: unknown flake output '<name>'` on every
      # single `nix flake check`, forever.
      apps = forAllSystems (
        pkgs:
        lib.mapAttrs (name: cmd: {
          type = "app";
          program = "${(wrappers pkgs).${name}}/bin/dev-${name}";
          meta.description = cmd.description;
        }) (commands pkgs)
      );

      # `nix develop` -- the toolchain, plus a dev-<verb> for every app.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = toolchain pkgs ++ lib.attrValues (wrappers pkgs) ++ [ (helpFor pkgs) ];

          env = envVars pkgs;

          # Some C extensions and node-gyp addons compile at -O0, where glibc's
          # _FORTIFY_SOURCE becomes a hard error instead of a warning.
          hardeningDisable = [ "fortify" ];

          shellHook = ''
            # mkShell inherits SOURCE_DATE_EPOCH=315532800 (1980-01-01) from
            # stdenv, and any wheel or zip built in here then dies with "ZIP does
            # not support timestamps before 1980".
            unset SOURCE_DATE_EPOCH

            ${rootPreamble}
            ${ldPreamble pkgs}
            ${envPreamble}

            # Nothing networked, nothing stateful and nothing interactive above
            # this line, and nothing below it either. No venv creation, no
            # `pio pkg install`, no `pip install`. Bootstrapping in the hook
            # makes a cold `nix develop -c dev-test` start downloading before it
            # runs anything, on EVERY invocation -- the exact failure an
            # unattended agent cannot diagnose. That is what `dev-setup` is for.

            # The banner is interactive-only, and this guard is load-bearing:
            # shellHook output lands on the STDOUT of `nix develop -c <cmd>`, so
            # an unguarded echo corrupts anything parsing it
            # (`nix develop -c cat x.json | jq` fails to parse). $- is the only
            # reliable discriminator here -- it lacks `i` for `nix develop -c`
            # and has it at an interactive prompt. Do not test $PS1 (unset in
            # both) or $IN_NIX_SHELL (set in both). >&2 is the second layer, for
            # the case where a caller runs us on a pty.
            case $- in
              *i*) echo "rgb-badge dev shell -- 'dev-help' for the command map" >&2 ;;
            esac
          '';
        };
      });

      # `nix flake check` -- honest by construction. NEVER add a check that
      # always passes: an agent reads "all checks passed!" as a signal, and a
      # fake check makes `nix flake check` a liar.
      checks = forAllSystems (
        pkgs:
        {
          # Realises the toolchain closure (so a typo'd or currently-broken attr
          # fails here) and builds every wrapper, which runs shellcheck over every
          # command text.
          toolchain =
            pkgs.runCommand "toolchain-check"
              {
                nativeBuildInputs = toolchain pkgs ++ lib.attrValues (wrappers pkgs);
              }
              ''
                for verb in ${lib.escapeShellArgs (lib.attrNames (commands pkgs))}; do
                  command -v "dev-$verb" > /dev/null || {
                    echo "dev-$verb is not on PATH" >&2
                    exit 1
                  }
                done
                touch "$out"
              '';

        }
        // lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
          # A real check, and the reason it exists is specific to this repo: the
          # interpreter above and KiCad's `_pcbnew.so` are coupled by CPython
          # ABI, and nothing else in this flake would notice if a nixpkgs bump
          # moved KiCad onto a different Python. Without pcbnew, 20 of the 22
          # Python files here do not run at all, so that drift deserves to fail
          # at the flake gate rather than mid-task. Hermetic and offline: it
          # imports the module and asserts the KiCad version is non-empty.
          #
          # Linux-only because kicad-base is marked broken on aarch64-darwin.
          pcbnew =
            pkgs.runCommand "pcbnew-import-check"
              {
                nativeBuildInputs = [ (pythonEnv pkgs) ];
                PYTHONPATH = pcbnewPath pkgs;
              }
              ''
                python3 -c '
                import pcbnew
                v = pcbnew.GetBuildVersion()
                assert v, "pcbnew.GetBuildVersion() returned nothing"
                print("pcbnew import OK, KiCad", v)
                '
                touch "$out"
              '';
        }
      );

      # `nix fmt` -- formats the *Nix* in this repo; project code is `dev-fmt`.
      # nixfmt-tree (the treefmt wrapper) rather than bare nixfmt, because bare
      # nixfmt tries to parse every path handed to it and fails on non-Nix files.
      # This file ships already formatted, so `nix fmt` is a no-op rather than a
      # diff.
      formatter = forAllSystems (pkgs: pkgs.nixfmt-tree);
    };
}
