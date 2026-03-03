<p align="center">
  <a href="https://github.com/rlaphoenix/minerva">Minerva Worker</a>
  <br/>
  <sup><em>Preserving Myrient's legacy, one file at a time.</em></sup>
</p>

<p align="center">
  <a href="https://github.com/rlaphoenix/minerva/blob/master/LICENSE">
    <img src="https://img.shields.io/:license-CC%201.0-blue.svg" alt="License">
  </a>
  <a href="https://pypi.org/project/minerva">
    <img src="https://img.shields.io/badge/python-3.12%2B-informational" alt="Python version">
  </a>
  <a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Onyx-Nostalgia/uv/refs/heads/fix/logo-badge/assets/badge/v0.json" alt="Manager: uv">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Linter: Ruff">
  </a>
  <a href="https://github.com/rlaphoenix/minerva/actions/workflows/ci.yml">
    <img src="https://github.com/rlaphoenix/minerva/actions/workflows/ci.yml/badge.svg" alt="Build status">
  </a>
</p>

* * *

Myrient is shutting down. Minerva is a volunteer-driven effort to archive its entire collection before it goes offline.
Run a script, share your bandwidth, help preserve the archive.

## Installation

Download and install the Python script from PIP/PyPI:

```shell
$ pip install minerva-worker
```

> [!NOTE]
If pip gives you a warning about a path not being in your PATH environment variable then promptly add that path then
close all open command prompt Windows, or running `minerva` won't work as it will not be recognized as a program.

You now have the `minerva` package installed - Voilà 🎉!  
Get started by running `minerva` in your Terminal or Windows Run.  
For configuration options, see help and options by running `minerva --help`.

*Alternatively, a Windows EXE is available on the [Releases] page, simply run it to begin!*

  [Releases]: <https://github.com/rlaphoenix/minerva/releases>

## Usage

It's very easy to use. Simply run the minerva.exe file, or run `minerva` in your Terminal/Command Prompt.

You can configure the worker settings by running `minerva run --help` to see what configuration options
you can change. If you have a great computer and network, it's recommended to bump up the -c and -b
options.

> [!TIP]
It's recommended to keep -c smaller or the same as -b.

## How it works

The worker script asks the minerva server for jobs to download. The server gives active workers random
missing needed file URLs to download. When the worker is given a job, it temporarily downloads the file
and uploads it to the minerva file servers. Once the file is downloaded, it is deleted from your machine.

> [!TIP]
If you also want a copy of the files, use the `--keep-files` setting.

Jobs are given exclusively to each worker, no two workers download the same file at the same time. However,
to verify that uploads aren't corrupted, each job gets given (eventually) to a second worker. Both uploads
are then confirmed and if both workers give back the same file to the minerva file server, then the job is
marked as complete and verified.

> [!NOTE]
You may see 409 Conflict errors on upload, this happens when either you or another worker had mismatching
files uploaded. Just ignore these error's and let the worker continue. If you suspect every file has this
issue, please verify your network connection is stable and verify your downloads arent corrupted.

## Discord Authentication

When using the minerva worker, you are prompted upon startup to login and authorize with Discord. This is
to authenticate unique users on the minerva server, to know who jobs are given to, and to use your username
and avatar in the worker dashboard leaderboards.

This does not give Minerva, this script, or anyone else access to your account, or any permissions.

## Docker
This section is for advanced users and requires some pre-existing familiarity with docker. The guide assumes docker is running in a unix environment.

### 1. Clone the repository
Clone the repository to somewhere on your device

### 2. Obtain a token
Obtain a token using this url: [`https://api.minerva-archive.org/auth/discord/login?worker_callback=http://127.0.0.1:19283/`](https://api.minerva-archive.org/auth/discord/login?worker_callback=http://127.0.0.1:19283/). It will ask for a connection to your discord account for authentication. This will only verify your account and will not store your discord token anywhere (it doesn't even have access to your discord token).

This will redirect to localhost and provide you with the token in the address bar. For example `http://127.0.0.1:19283/?token=1234`, where `1234` is your token.

Then place your token in a file in your home directory at `~/minerva/token`.

```bash
echo -n "<token>" > ~/minerva/token
```

### Start the container
Bring up the container with `docker compose up -d` from the root of the repository. This will build the package from source, start the worker, and then read the token from the bind-mounted volume `~/minerva`

## Development

1. Install [uv]
2. `uv sync --all-extras --all-groups`
3. `.venv\Scripts\activate` (or `source .venv/bin/activate` on macOS and Linux)
4. `uv tool install pre-commit --with pre-commit-uv --force-reinstall`
5. `pre-commit install`

Now feel free to work on the project however you like, all code will be checked before committing.

  [uv]: <https://docs.astral.sh/uv>

## Credit

- [bl791] for the original one-file script.
- [Puyodead1] for their improved rich interface and speedups.
- [rlaphoenix] for further improvements, bug fixes, support.
- [wikipiti] for the aria2 control file parsing code.

  [bl791]: <https://github.com/bl791>
  [Puyodead1]: <https://github.com/Puyodead1>
  [rlaphoenix]: <https://github.com/rlaphoenix>
  [wikipiti]: <https://github.com/wikipiti>

## Licensing

This software is licensed under the terms of [CC0 1.0 Universal](LICENSE).
You can find a copy of the license in the LICENSE file in the root folder

* * *

© rlaphoenix 2026
