# Installation

## Installing from PyPI

To install from PyPI, run the following command:

<div class="termy">

```console
$ pip install CTF-Architect
---> 100%
Successfully installed CTF-Architect
```

</div>

!!! warning
    If the above command produces an error during installation, try running the command in a terminal with administrator privileges.


## Installing from Source

!!! warning
    Installing from source will pull the latest changes from the repository. This may include new features, bug fixes, or breaking changes. If you want to use a stable version, it is recommended to install from PyPI.

Git clone the repository, and pip install it

<div class="termy">

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
---> 100%
Successfully installed CTF-Architect
```

</div>

## Post Installation

If the installation is successful, you should be able to run the following commands:

<div class="termy">

```console
$ ctf-architect --help

 Usage: ctf-architect [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────╮
│ --install-completion          Install completion  │
│                               for the current     │
│                               shell.              │
│ --show-completion             Show completion for │
│                               the current shell,  │
│                               to copy it or       │
│                               customize the       │
│                               installation.       │
│ --help                        Show this message   │
│                               and exit.           │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ challenge  Commands to manage challenges in the   │
│            CTF repo.                              │
│ docker     Commands to manage challenge services  │
│            in the CTF repo.                       │
│ init       Initialize a new CTF repository.       │
│ mapping    Commands to manage port mappings for   │
│            challenge services                     │
│ stats      Commands to manage challenge           │
│            statistics in the challenge repository │
╰───────────────────────────────────────────────────╯

$ chall-architect --help

 Usage: chall-architect [OPTIONS]

 Creates a challenge folder in the current directory

╭─ Options ─────────────────────────────────────────╮
│ --install-completion          Install completion  │
│                               for the current     │
│                               shell.              │
│ --show-completion             Show completion for │
│                               the current shell,  │
│                               to copy it or       │
│                               customize the       │
│                               installation.       │
│ --help                        Show this message   │
│                               and exit.           │
╰───────────────────────────────────────────────────╯
```

</div>

!!! note
    If after installation, you get an error saying that the command is not found, you may need to add the python scripts folder to your PATH environment variable. See [this guide](https://realpython.com/add-python-to-path/) for more information.

Now that you have successfully installed CTF-Architect, read these guides to get started:

- [Packaging a challenge for submission](./packaging-challenges.md)
- [Setting up a challenge repository](./repository-setup.md)
