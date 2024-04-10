# Challenge Specification v0.1
This page describes the structure of a challenge in CTF-Architect.

## Challenge Structure
A challenge in CTF-Architect is a directory that contains the following files and directories:

```
.
└── 📁 {challenge_name}/
    ├── 📁 dist/
    │   └── 📄...
    ├── 📁 service/
    │   ├── 📁 {service_name}/
    │   │   ├── 📄...
    │   │   └── 🐋 Dockerfile
    │   └── 🐋 docker-compose.yml
    ├── 📄 chall.toml
    └── 📄 README.md
```

| File/Directory | Description |
| -------------- | ----------- |
| `dist/` | Directory containing the challenge files to give to users attempting the challenge. |
| `service/` | Directory containing the services for challenges that require hosting. |
| `service/{service_name}/` | Directory containing the files for the service. This folder must container a `Dockerfile` |
| `service/docker-compose.yml` | Docker Compose file to run the services. If only one service is needed, this does not need to be added. |
| `chall.toml` | TOML file containing the metadata for the challenge. This is generated automatically by `chall-architect` |
| `README.md` | Markdown file containing the description of the challenge. This is generated automatically by `chall-architect` |

## `chall.toml` Specification
The `chall.toml` file contains the metadata for the challenge. The file is in the following format:

```toml
# Challenge info file (version 0.1)
# This file is machine generated. DO NOT EDIT unless you know what you are doing.
# If you want to create or edit a challenge, use chall-architect instead.

version = "0.1"

[challenge]
author = "Author Name"
category = "category"
description = "Description"
difficulty = "difficulty"
name = "Challenge Name"

files = [
    "file1",
    "file2"
]

requirements = [
    "challenge1",
    "challenge2"
]

[challenge.extras]
discord = "juscodin"


# Static case-sensitive flag
[[challenge.flags]]
flag = "flag{example}"

# Static case-insensitive flag
[[challenge.flags]]
flag = "flag{example2}"
case_insensitive = true

# Regex case-sensitive flag
[[challenge.flags]]
flag = "flag{example3}"
regex = true

# Regex case-insensitive flag
[[challenge.flags]]
flag = "flag{example4}"
regex = true
case_insensitive = true


# Example hint
[[challenge.hints]]
cost = 10
content = "This is a hint"

# Example hint with requirements
[[challenge.hints]]
cost = 20
content = "This is a hint with requirements"
requirements = 0


# Example service
[[challenge.services]]
name = "service1"
path = "service1"
port = 1337
type = "web"
```

### Fields
- `author` (String): Author of the challenge
- `category` (String): Category of the challenge
- `description` (String): Description of the challenge
- `difficulty` (String): Difficulty of the challenge
- `name` (String): Name of the challenge
- `files` (List of Strings) (Optional): List of files to give users attempting the challenge. The files are specified as a list of strings, where each string is a path to a file. The paths are relative to the challenge's directory. You can also specify a URL for users to download the file from. If you have no files to give, you do not need to specify this.
- `requirements` (List of Strings) (Optional): List of challenge names for challenges that must be completed before this challenge can be attempted. If there are no requirements, you do not need to specify this.
- `extras` (Table) (Optional): Extra information about the challenge. Extra fields specified in the CTF repository config must be specified here.
- `flags` (List of Tables): List of flags for the challenge. Flags can be static or regex. The flag must have the following fields:
    - `flag` (String): The flag for the challenge
    - `regex` (Boolean) (Optional): Whether the flag is a regex. Default is `false`.
    - `case_insensitive` (Boolean) (Optional): Whether the flag is case-insensitive. Default is `false`.
- `hints` (List of Tables) (Optional): List of hints for the challenge. Hints can have a cost and requirements. The hint must have the following fields:
    - `cost` (Integer): The cost of the hint
    - `content` (String): The content of the hint
    - `requirements` (Integer) (Optional): The index of the hint that must be purchased before this hint can be purchased.
- `services` (List of Tables) (Optional): List of services for the challenge. The service must have the following fields:
    - `name` (String): Name of the service
    - `path` (String): Path to the service directory, relative to the root of the challenge folder
    - `port` (Integer): Port the docker container exposes
    - `type` (String): The type of service. This must be one of the following:
        - `web`     : A web service, must have a port exposed
        - `nc`      : A netcat service, must have a port exposed
        - `ssh`     : An ssh service, must have a port exposed
        - `secret`  : A secret service, it must have a port exposed, but will not be shown in the challenge info. This is useful for challenges where the service must be discovered by the player
        - `internal`: An internal service, does not need to expose a port, and will not be shown in the challenge info. This is useful for challenges where the service should not be accessed directly, i.e. web admin bots
