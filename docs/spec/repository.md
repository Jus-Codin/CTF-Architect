# Challenge Repository Specification v0.1

!!! warning

    The Challenge Repository Specification is a work in progress and is subject to change. It will be kept at `v0.1` until the specification is stable.


## Challenge Repository Structure
A Challenge Repository is a directory that contains all the challenges for a CTF. It has the following structure:

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
The following is an example of a `ctf_config.toml` file that contains all possible fields:
```toml
# CTF Repo Config File (version 0.1)
# This file is machine generated. DO NOT EDIT unless you know what you are doing.
# This is the file to specify to chall-architect when creating a new challenge

version = "0.1"

[config]
categories = ["misc", "web", "forensics", "crypto", "reverse", "pwn"]
starting_port = 8000
name = "Demo CTF"
extras = []

[[config.difficulties]]
name = "easy"
value = 500

[[config.difficulties]]
name = "medium"
value = 500

[[config.difficulties]]
name = "hard"
value = 500
```

## Fields

### categories
A list of categories for the challenges in the repository.

```toml
categories = ["misc", "web", "forensics", "crypto", "reverse", "pwn"]
```

### starting_port
The port number to start assigning to services.

```toml
starting_port = 8000
```

### name
The name of the CTF.

```toml
name = "Demo CTF"
```

### extras (optional)
A list of extra fields that challenges added to this repository must specify.

```toml
extras = []
```

### difficulties
A list of difficulties for the challenges in the repository. Must have the following fields:

- `name`: The name of the difficulty.
- `value`: The value of challenges with this difficulty.

```toml
[[config.difficulties]]
name = "easy"
value = 500
```
