# Packaging Challenges

!!! note
    This guide assumes that you have successfully installed CTF-Architect. If you have not, please refer to the [installation guide](../installation.md).


## Download ctf_config.toml
Download the relavant `ctf_config.toml` file for the CTF. This is required to properly package the challenge. If you do not have this file, contact the CTF organizers for it.

## Prepare Your Files
Prepare the following files for your challenge:

- **Source Files**: The source files, e.g. precompiled binaries, scripts, etc for the challenge.
- **Solution Files**: The writeup or solution files for the challenge.
- **Challenge Files**: The files that the participants will interact with to solve the challenge.
- **Service Folders**: If your challenge requires a service, create a folder for the service. This folder should contain the files required to run the service and a `Dockerfile`.

## Packaging a Challenge
To package a challenge for submission, run the following command:

```console
$ ctfa chall new
```

!!! note
    The `ctfa chall new` command will create the challenge directory structure in a new folder in the current directory. If you would like it to be created in the current directory, use the `ctfa chall init` command instead.

```console
$ ctfa chall new

Please select the Repo Configuration file.
╭─ CTF Config ──────────────────────────────────────────────────────────╮
│  CTF Name: Test CTF                                                   │
│  Flag Format: flag{.*}                                                │
│  Starting Port: 8000                                                  │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Categories ──────────────────────────────────────────────────────────╮
│   - Web                                                               │
│   - Pwn                                                               │
│   - Osint                                                             │
│   - Forensics                                                         │
│   - Re                                                                │
│   - Misc                                                              │
│   - Crypto                                                            │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Difficulties ────────────────────────────────────────────────────────╮
│   - Easy                                                              │
│   - Medium                                                            │
│   - Hard                                                              │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Extras ──────────────────────────────────────────────────────────────╮
│   - discord (string)                                                  │
╰───────────────────────────────────────────────────────────────────────╯
Is this the correct Repo Configuration? Yes

🚀 Enter the challenge name: Example Challenge

📝 Would you like to specify the folder name manually? Yes
🚀 Enter the challenge folder name: example-challenge

Press Ctrl-D (or Ctrl-Z on Windows) to finish input.
📝 Enter the challenge description:

This is an example challenge desciption
^Z

🏷 Select the challenge category: misc

📊 Select the challenge difficulty: easy

👤 Enter the challenge author: JusCodin

Enter your discord tag: example

Would you like to specify the requirements for the challenge? Yes
⚙ Enter a requirement: Example Requirement
Do you want to add another requirement? No

🚩 Select the type of flag to add: Static
Is the flag case-insensitive? No
🚩 Enter the flag: flag{test}
Would you like to add another flag? No

💡 Does the challenge have hints? Yes
Press Ctrl-D (or Ctrl-Z on Windows) to finish input.
💡 Enter the hint:

This is a hint
^Z
💰 Enter the hint cost: 100
Would you like to add another hint? No

Does the challenge have distributable files? Yes
Select the type of files to add: Local file
How would you like to select the file?: Browse for file
Added file: C:/example-file.txt

Select the type of files to add: URL
📁 Enter the URL of the file: http://example-file.com
Added URL: http://example-file.com

Select the type of files to add: Done

Does the challenge have source files? No

Does the challenge have solution files? No

💻 Would you like to import a service into this challenge? Yes
💻 Select the service type: TCP
💻 Enter the service name: example-service
💻 Enter the service port: 5000
Would you like to add another port? Yes
💻 Enter the service port: 5001
Would you like to add another port? No
How would you like to select the folder?: Browse for folder
Selected folder: C:/Example-Service
Would you like to add another service? No

╭─ ⚙ Challenge Config ──────────────────────────────────────────────────╮
│  Name: Example Challenge                                              │
│  Author: JusCodin                                                     │
│  Category: Misc                                                       │
│  Difficulty: Easy                                                     │
│  Description: This is an example challenge desciption                 │
│                                                                       │
│  Folder Name: example-challenge                                       │
╰───────────────────────────────────────────────────────────────────────╯
╭─ ⚙ Requirements ──────────────────────────────────────────────────────╮
│   - Example Requirement                                               │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 📦 Extras ───────────────────────────────────────────────────────────╮
│   - discord: example                                                  │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 💡 Hints ────────────────────────────────────────────────────────────╮
│   - This is a hint                                                    │
│  (100 points)                                                         │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 📁 Dist Files ───────────────────────────────────────────────────────╮
│   - C:\example-file.txt                                               │
│   - http://example-file.com                                           │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 📁 Source Files ─────────────────────────────────────────────────────╮
│   - None                                                              │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 📁 Solution Files ───────────────────────────────────────────────────╮
│   - None                                                              │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 🚩 Flags ────────────────────────────────────────────────────────────╮
│ ┏━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓                            │
│ ┃ Flag       ┃ Type   ┃ Case-Insensitive ┃                            │
│ ┡━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩                            │
│ │ flag{test} │ static │ False            │                            │
│ └────────────┴────────┴──────────────────┘                            │
╰───────────────────────────────────────────────────────────────────────╯
╭─ 💻 Services ─────────────────────────────────────────────────────────╮
│ ┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┓ │
│ ┃ Service Name    ┃ Path                        ┃ Ports      ┃ Type ┃ │
│ ┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━┩ │
│ │ example-service │ C:/Example-Service          │ 5000, 5001 │ tcp  │ │
│ └─────────────────┴─────────────────────────────┴────────────┴──────┘ │
╰───────────────────────────────────────────────────────────────────────╯
Is the challenge configuration correct? Yes
✨ Challenge initialized successfully! ✨
```

## Linting the Challenge
To ensure that the challenge is correctly formatted, you can lint the challenge to find any potential issues. To do this, run the following command in the challenge directory:

```console
$ ctfa chall lint
Would you like to select a CTF config file? Yes
Please select the Repo Configuration file.
╭─ CTF Config ──────────────────────────────────────────────────────────╮
│  CTF Name: Test CTF                                                   │
│  Flag Format: flag{.*}                                                │
│  Starting Port: 8000                                                  │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Categories ──────────────────────────────────────────────────────────╮
│   - Web                                                               │
│   - Pwn                                                               │
│   - Osint                                                             │
│   - Forensics                                                         │
│   - Re                                                                │
│   - Misc                                                              │
│   - Crypto                                                            │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Difficulties ────────────────────────────────────────────────────────╮
│   - Easy                                                              │
│   - Medium                                                            │
│   - Hard                                                              │
╰───────────────────────────────────────────────────────────────────────╯
╭─ Extras ──────────────────────────────────────────────────────────────╮
│   - discord (string)                                                  │
╰───────────────────────────────────────────────────────────────────────╯
Is this the correct Repo Configuration? Yes
╭─────────────────── example-challenge Lint Results ────────────────────╮
│ example-challenge (all passed)                                        │
│ └── ✓ All checks passed                                               │
╰───────────────────────────────────────────────────────────────────────╯
```

## Submitting the Challenge
Once you have packaged the challenge, you can submit it to the CTF organizers. To do this, compress the challenge folder into a `.zip` file and send it to the organizers.

!!! tip
    You can actually submit multiple challenges at once by compressing multiple challenge folders into a single `.zip` file. However, if your organization requires you to submit challenges individually, you should follow their guidelines.
    