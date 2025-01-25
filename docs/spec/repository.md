# Challenge Repository Specification v0.1

## Challenge Repository Structure

```
.
└── 📁 {repo_name}/
    ├── 📁 challenges/
    │   ├── 📁 {category_name}/
    │   │   ├── 📁 ...
    │   │   └── 📄 README.md
    │   ├── 📁 ...
    │   └── 📄 README.md
    └── 📄 ctf_config.toml
```

| File/Directory | Description |
| -------------- | ----------- |
| `challenges/` | Directory containing folders for each challenge category specified in the `ctf_config.toml` file. |
| `challenges/{category_name}/` | Directory containing the challenges for that category. |
| `README.md` | Markdown file containing information such as the difficulty distribution, challenge info, and services. |
| `ctf_config.toml` | TOML file containing metadata about the repository. |


## Example

```toml
# CTF Repository Metadata File (version 0.1)
# This file is machine generated. DO NOT EDIT unless you know what you are doing.
# This is the file to specify to ctf-architect when creating a new challenge.

# ----------------- CTF Config Specification Version (required) ------------------
version = "0.1"


# --------------------------- CTF Config Info (required) -------------------------
# This section specifies the information about the CTF repository.
# Some fields are required, while others are optional:
# - categories: The categories of challenges
# - difficulties: The difficulties of challenges
# - flag_format (optional): The format of the flags
# - starting_port (optional): The starting port for the challenge services
# - name: The name of the CTF

[config]
categories = ["web", "crypto", "pwn", "re", "misc", "forensics", "osint"]
difficulties = ["easy", "medium", "hard"]
flag_format = "flag{.*}"
starting_port = 8000
name = "Demo CTF"


# ------------------------- CTF Config Extras (optional) -------------------------
# This section specifies extra fields that challenges should have.
# The fields can be required or optional, and can be of the following types:
# - string: A string value
# - integer: An integer value
# - float: A float value
# - boolean: A boolean value
#
# The fields are specified as a list of tables, where each table has the following fields:
# - name: The name of the field
# - description: The description of the field
# - prompt: The prompt to display to the user when entering the field
# - required: Whether the field is required or not
# - type: The type of the field
[[config.extras]]
name = "discord"
description = "Discord username"
prompt = "Enter your Discord username"
required = true
type = "string"
```

## Fields

### categories
A list of valid categories for the challenges in the repository.

```toml
categories = ["misc", "web", "forensics", "crypto", "reverse", "pwn"]
```

### difficulties
A list of valid difficulties for the challenges in the repository.

```toml
difficulties = ["easy", "medium", "hard"]
```

### name
The name of the CTF.

```toml
name = "Demo CTF"
```

### flag_format (optional)
Flag format that static flags in challenges have to follow.

```toml
flag_format = "flag{.*}"
```

### starting_port (optional)
The port number to start assigning to services with.

If you are using CTF Architect to deploy challenges, you must specify this field.

```toml
starting_port = 8000
```

### extras (optional)
A list of extra fields that challenges added to this repository must specify.

Example:
```toml
[[config.extras]]
name = "discord"
description = "Discord username"
prompt = "Enter your Discord username"
required = true
type = "string"
```

## Extras Fields

### name
The name of the extra field.

```toml
name = "discord"
```

### description
A description of the field.

```toml
description = "Discord username of the author"
```

### prompt
The prompt to display to the user when entering the field.

```toml
prompt = "Enter your Discord username"
```

### required
Whether the field is required or not.

```toml
required = true
```

### type
The type of the field. Must be one of the following:

- `string` : A string value
- `integer`: An integer value
- `float`  : A float value
- `boolean`: A boolean value

```toml
type = "string"
```
