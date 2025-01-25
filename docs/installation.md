# Installation

## Installing from PyPI

To install from PyPI, run the following command:

```console
$ pip install CTF-Architect
```

## Installing from Source

!!! danger
    Installing from source will pull the latest changes from the repository. This may include new features, bug fixes, or breaking changes. If you want to use a stable version, it is recommended to install from PyPI.

Git clone the repository, and pip install it

```console
$ git clone https://github.com/Jus-Codin/CTF-Architect
Cloning into 'CTF-Architect'...
remote: Enumerating objects: 496, done.
remote: Counting objects: 100% (78/78), done.
remote: Compressing objects: 100% (55/55), done.
remote: Total 496 (delta 32), reused 44 (delta 23), pack-reused 418
Receiving objects: 100% (496/496), 941.69 KiB | 15.44 MiB/s, done.
Resolving deltas: 100% (240/240), done.

$ cd CTF-Architect

$ pip install .
```

## Post Installation

!!! note
    After installation, you may need to add the python scripts folder to your PATH environment variable. See [this guide](https://realpython.com/add-python-to-path/) for more information.

If the installation is successful, you should be able to run the `ctfa` cli:

```console
$ ctfa
Usage: ctfa COMMAND

╭─ Commands ──────────────────────────────────────────────────╮
│ --help -h  Display this message and exit.                   │
│ --version  Display application version.                     │
╰─────────────────────────────────────────────────────────────╯
╭─ Subcommands ───────────────────────────────────────────────╮
│ chall  Commands for creating and editing challenges.        │
│ repo   Commands for managing the challenge repository.      │
╰─────────────────────────────────────────────────────────────╯
```

Now that you have successfully installed CTF-Architect, read these guides to get started:

- [Packaging a challenge for submission](./guides/packaging-challenges.md)
- [Setting up a challenge repository](./guides/repository-setup.md)