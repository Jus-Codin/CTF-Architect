# Setting up a challenge repository

!!! note
    This guide assumes that you have already installed CTF-Architect. If you haven't, see the [installation guide](../installation.md).

## Create a new repository
To create a new challenge repository, run the following command:

```console
$ ctfa repo init
Enter the name of the CTF: Example CTF
CTF Name: Example CTF
Enter the flag format: flag{.*}

Would you like to specify a starting port? Yes
Enter the starting port: 8000
Starting Port: 8000

───────────────────────── Challenge Categories ──────────────────────────
Enter the categories for the CTF (one per line, empty line to stop).
Category Name (empty to stop): web
Category "web" added.

Category Name (empty to stop): forensics
Category "forensics" added.

Category Name (empty to stop): crypto

Category Name (empty to stop): misc

Category Name (empty to stop): re

Category Name (empty to stop): pwn

Category Name (empty to stop): osint

Category Name (empty to stop):
Categories:
  - Web
  - Forensics
  - Crypto
  - Misc
  - Re
  - Pwn
  - Osint

Enter the difficulties for the CTF (empty name to stop).
Difficulty Name (empty to stop): easy
Difficulty "easy" added.

Difficulty Name (empty to stop): medium
Difficulty "medium" added.

Difficulty Name (empty to stop): hard
Difficulty "hard" added.

Difficulty Name (empty to stop): insane
Difficulty "insane" added.

Difficulty Name (empty to stop):
Difficulties:
  - Easy
  - Medium
  - Hard
  - Insane

───────────────────────────── Extra Fields ──────────────────────────────
Would you like to specify extra fields for challenges? Yes

Extra Field Name (empty to cancel): discord
Extra Field Description: The discord tag of the challenge creator
Extra Field Prompt (shown to challenge creators): Enter your discord tag
Is this extra field required? Yes
Extra Field Type: string
Extra Field "discord" added.
Add another extra field? No
Extra Fields:
  - discord (string)
╭─ CTF Config ──────────────────────────────────────────────────────────╮
│  CTF Name: Example CTF                                                │
│  Flag Format: flag{.*}                                                │
│  Starting Port: 8000                                                  │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Categories ──────────────────────────────────────────────────────────╮
│   - Web                                                               │
│   - Forensics                                                         │
│   - Crypto                                                            │
│   - Misc                                                              │
│   - Re                                                                │
│   - Pwn                                                               │
│   - Osint                                                             │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Difficulties ────────────────────────────────────────────────────────╮
│   - Easy                                                              │
│   - Medium                                                            │
│   - Hard                                                              │
│   - Insane                                                            │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Extras ──────────────────────────────────────────────────────────────╮
│   - discord (string)                                                  │
╰───────────────────────────────────────────────────────────────────────╯
Are you sure you want to create this Challenge Repository? Yes
✨ Challenge repository initialized! ✨
```

This will create a new challenge repository in the current directory. The repository will contain a `ctf_config.toml` file with the specified metadata.

## Add challenges to the repository
To add a new challenge to the repository, add the zipped challenges to the root of the repository, run the following command:

```console
$ ctfa repo import
Successfully imported example-challenge
Updating stats...
✨ Repository stats updated.
✨ Successfully imported 1 challenges. ✨
```

Once the challenges are imported, the repository will be updated with the new challenges. You can then proceed to manually delete the zipped challenges from the repository.

## Lint the repository
To check the repository for any potentially problematic challenges, run the following command:

```console
$ ctfa repo lint
╭──────────────────────────── Lint Results ─────────────────────────────╮
│ challenges/ (1 failed)                                                │
│ ├── web/ (all passed)                                                 │
│ │   └── ✓ All challenges passed                                       │
│ ├── forensics/ (all passed)                                           │
│ │   └── ✓ All challenges passed                                       │
│ ├── crypto/ (all passed)                                              │
│ │   └── ✓ All challenges passed                                       │
│ ├── misc/ (1 failed)                                                  │
│ │   └── example-challenge (2 violations)                              │
│ │       ├── ⚠ F002 - No writeup.md with content in solution folder    │
│ │       │   found                                                     │
│ │       └── ✕ C011 - Requirements in chall.toml file could not be     │
│ │           found or loaded:                                          │
│ │             - Example Requirement                                   │
│ ├── re/ (all passed)                                                  │
│ │   └── ✓ All challenges passed                                       │
│ ├── pwn/ (all passed)                                                 │
│ │   └── ✓ All challenges passed                                       │
│ └── osint/ (all passed)                                               │
│     └── ✓ All challenges passed                                       │
╰───────────────────────────────────────────────────────────────────────╯
```

Additionally, you may also specify challenges to lint:

```console
$ ctfa repo lint example-challenge
╭─────────────────── example-challenge Lint Results ────────────────────╮
│ example-challenge (2 violations)                                      │
│ ├── ⚠ F002 - No writeup.md with content in solution folder found      │
│ └── ✕ C011 - Requirements in chall.toml file could not be found or    │
│     loaded:                                                           │
│       - Example Requirement                                           │
╰───────────────────────────────────────────────────────────────────────╯
```

!!! note
    This is equivalent to running `ctfa chall lint example-challenge`, except the `ctf_config.toml` file is automatically loaded.
