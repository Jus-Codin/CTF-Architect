# Challenge Specification v0.1

## Challenge Folder Structure

```
.
└── 📁 {challenge_name}/
    ├── 📁 src/
    │   └── 📄...
    ├── 📁 dist/
    │   └── 📄...
    ├── 📁 service/
    │   ├── 📁 {service_name}/
    │   │   ├── 📄...
    │   │   └── 🐋 Dockerfile
    │   └── 🐋 compose.yml (optional)
    ├── 📁 solution/
    │   └── 📄...
    ├── 📄 chall.toml
    └── 📄 README.md
```

| File/Directory | Description |
| -------------- | ----------- |
| `src/` | Directory containing the source files for the challenge. This is used to assist testing, not for giving to users attempting the challenge. |
| `dist/` | Directory containing the challenge files to give to users attempting the challenge. |
| `service/` | Directory containing the services for challenges that require hosting. |
| `service/{service_name}/` | Directory containing the files for the service. This folder must contain a `Dockerfile` |
| `service/compose.yml` | Docker Compose file to run the services. Useful if extra configurations in the compose file is needed for the challenge to work. This file will be added directly to the root compose file in the repo using the [`include`](https://docs.docker.com/compose/multiple-compose-files/include/) element. |
| `solution/` | Directory containing the solution files for the challenge. This is used to assist testing, not for giving to users attempting the challenge. |
| `chall.toml` | TOML file containing the metadata for the challenge. This is generated automatically. |
| `README.md` | Markdown file containing a text summary of the challenge's details. This is generated automatically.` |


## Example

```toml
# Challenge Metadata File (version 0.1)
# This file is machine generated. DO NOT EDIT unless you know what you are doing.
# If you want to create or edit a challenge, use the CLI instead.

# ------------------- Challenge Specification Version (required) -------------------
version = "0.1"


# --------------------------- Challenge Info (required) ----------------------------
# This section specifies the information about the challenge.
# The section must have the following fields:
# - author: The author of the challenge
# - category: The category of the challenge
# - description: The description of the challenge
# - difficulty: The difficulty of the challenge
# - name: The name of the challenge
[challenge]
author = "Author Name"
category = "category"
description = "Description"
difficulty = "difficulty"
name = "Challenge Name"

# ------------------------ Challenge Folder Name (optional) ------------------------
# Specifies the folder name to use to store the challenge files.
# If not specified, the folder name will be generated from the challenge name.
# Must be a valid folder name, restricted to the pattern \^[a-zA-Z][a-zA-Z0-9 _-]*$\

folder_name = "folder_name"


# --------------------------- Challenge Files (optional) ---------------------------
# Specifies the files that are part of the challenge.
# The files are specified as a list of strings, where each string is a path to a file.
# The paths are relative to the challenge directory.
# Alternatively, specify a URL to download the file from the internet.

files = [
    "file1",
    "file2"
]

# ----------------------- Challenge Requirements (optional) ------------------------
# Specifies the challenges that must be solved before this challenge can be unlocked.
# The requirements are specified as a list of strings, where each string is the name of a challenge.

requirements = [
    "challenge1",
    "challenge2"
]


# ------------------------ Challenge Extra Info (optional) -------------------------
# This section specifies extra information about the challenge.
# The fields in this section must be specified if it is required by the ctf_config.toml file

[challenge.extras]
discord = "a_discord_username"


# --------------------------- Challenge Flags (required) ---------------------------
# Specifies the flags that are part of the challenge.
# To specify multiple flags, create another table in the array of tables.
# The flag table must have the following fields:
# - flag: The flag value
# - regex (optional): If the flag is a regex flag, otherwise it is a static flag. Defaults to false
# - case_insensitive (optional): If the flag is case insensitive or not. Defaults to false

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


# --------------------------- Challenge Hints (optional) ---------------------------
# Specifies the hints that are part of the challenge.
# To specify multiple hints, create another table in the array of tables.
# The hint table must have the following fields:
# - cost: The cost of the hint
# - content: The content of the hint
# - requirements (optional): The requirements to unlock the hint. This should be
#   an index referencing a hint in the array of tables. Defualts to null

# Example hint
[[challenge.hints]]
cost = 10
content = "This is a hint"

# Example hint with requirements
[[challenge.hints]]
cost = 20
content = "This is a hint with requirements"
requirements = 0


# ------------------------- Challenge Services (optional) --------------------------
# Specifies the services that are part of the challenge.
# To specify multiple services, create another table in the array of tables.
# The service table must have the following fields:
# - name: The name of the service. This will be the name of the docker container. Restricted to [a-z0-9_-] and must be unique
# - path: The path to the service's directory. This path is relative to the challenge directory
# - port: The port that the docker container exposes. This is an integer. Only one of port or ports should be specified
# - ports: The ports that the docker container exposes. This is an array of integers. Only one of port or ports should be specified
# - type: The type of the service. This must be one of the following:
#   - web      : A web service, must have a port exposed
#   - tcp      : A tcp service, must have a port exposed
#   - ssh      : An ssh service, must have a port exposed
#   - secret   : A secret service, it must have a port exposed, but will not be shown in the challenge info
#                This is useful for challenges where the service must be discovered by the player
#   - internal : An internal service, does not need to expose a port, and will not be shown in the challenge info
#                This is useful for challenges where the service should not be accessed directly, i.e. web admin bots

# Example service
[[challenge.services]]
name = "service1"
path = "service1"
port = 1337
type = "web"

# Extra service info (optional)
[challenge.services.extras]
privileged = true  # Make the docker container privileged
```

## Fields

### author
Defines the author of the challenge. Must be a string.
```toml
author = "Author Name"
```

### category
Specifies the category of the challenge. This should be a lowercase string, and must be located in the [`categories`](./repository.md#categories) field in the CTF repository config.
```toml
category = "category"
```

### description
Description of the challenge. This can be a multi-line string.
```toml
description = "Description"
```

```toml
description = """This is a multi-line description
of the challenge"""
```

### difficulty
Specifies the difficulty of the challenge. This should be a lowercase string, and must be located in the [`difficulties`](repository.md#difficulties) field in the CTF repository config.
```toml
difficulty = "difficulty"
```

### name
Name of the challenge. If the `folder_name` field is not provided, this will be used to generate the folder name for the challenge by substituting using the regex expression `/^[^a-zA-Z]+|[^a-zA-Z0-9 _-]/`.
```toml
name = "Challenge Name"
```

### files (optional)
List of files to give users attempting the challenge. Each item in the list can either be a path or a URL. Paths must be relative to the challenge directory.
```toml
files = [
    "http://example.com/file1",
    "./dist/file2"
]
```

### requirements (optional)
List of challenge names for challenges that must be completed before this challenge can be attempted.
```toml
requirements = [
    "challenge1",
    "challenge2"
]
```

### folder_name (optional)
Specify the folder name for the challenge. Must follow the pattern `/^[a-zA-Z][a-zA-Z0-9 _-]*$/`. This is useful if you want to have a challenge name that cannot be converted to a folder name. (e.g. `🦈 -> [empty_string]`)
```toml
folder_name = "challenge_name"
```

### extras (optional)
Extra information about the challenge. Extra fields specified in the [CTF repository config](./repository.md#extras) must be specified here.
```toml
[challenge.extras]
discord = "foobar"
```

### flags
List of flags for the challenge. Apart from the `flag` field, the following fields can be optionally specified:

- `regex` (Boolean): Whether the flag is a regex expression. Default is `false`.
- `case_insensitive` (Boolean): Whether the flag is case-insensitive. Default is `false`.

Examples:
```toml
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
```

### hints (optional)
List of hints for the challenge. Each hint must have the following fields:

- `cost` (Integer): The cost of the hint
- `content` (String): The content of the hint
- `requirements` (Integer) (Optional): The index of the hint that must be purchased before this hint can be purchased.

Examples:
```toml
# Example hint
[[challenge.hints]]
cost = 10
content = "This is a hint"

# Example hint with requirements
[[challenge.hints]]
cost = 20
content = "This is a hint with requirements"
requirements = 0
```

### services (optional)
List of services for the challenge. A service is allows you to specify configurations for a docker container that will be used to host the challenge.

Examples:
```toml
# Example service
[[challenge.services]]
name = "service1"
path = "./service/service1"
port = 1337
type = "web"

# Example service with multiple ports
[[challenge.services]]
name = "service2"
path = "./service/service2"
ports = [1337, 1338]
type = "nc"

# Example service with extras
[[challenge.services]]
name = "service3"
path = "./service/service3"
port = 1337
type = "web"

[challenge.services.extras]
privileged = true
```

## Service Fields

### name
The name of the service. Must be a string.
```toml
name = "service1"
```

### path
Path to the service directory, relative to the root of the challenge folder. Must be a string.
```toml
path = "./service/service1"
```

### port (optional)
Port the docker container exposes. Must be specified unless `ports` is specified or `type` is `"internal"`. Must be an integer.
```toml
port = 1337
```

### ports (optional)
List of ports the docker container exposes. Must be specified unless `port` is specified or `type` is `"internal"`. Must be a list of integers.
```toml
ports = [1337, 1338]
```

### type
The type of service. Must be one of the following:

- `web`     : A web service, must have a port exposed
- `tcp`     : A tcp service, must have a port exposed
- `ssh`     : An ssh service, must have a port exposed
- `secret`  : A secret service, it must have a port exposed, but will not be shown in the challenge info. This is useful for challenges where the service must be discovered by the player
- `internal`: An internal service, does not need to expose a port, and will not be shown in the challenge info. This is useful for challenges where the service should not be accessed directly, i.e. web admin bots

```toml
type = "web"
```

### extras (optional)
Extra configurations for the service to be passed to the docker compose file.

!!! warning

    The configurations set here will not overwrite configurations generated by `ctf-architect`.

The following service configuration:
```toml
[[challenge.services]]
name = "service1"
path = "./service/service1"
port = 1337
type = "web"

[challenge.services.extras]
privileged = true
```

Will look similar to this in the generated docker compose file:
```yaml
networks:
  challengename-network: {}

services:
  challenge_name-service1:
    build: ./service/service1
    container_name: challenge_name-service1
    networks:
    - challengename-network
    ports:
    - 8000:1337
    privileged: true
    restart: always
```
