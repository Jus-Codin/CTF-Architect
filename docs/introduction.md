# CTF Architect Overview

CTF Architect is a command-line tool for standardised challenge creation and management.

It consists of 2 main commands:

- `ctfa repo`: Commands for managing the challenge repository.
- `ctfa chall`: Commands for creating and editing challenges.

## How it works

CTF Architect is centered around 2 TOML configuration files - `ctf_config.toml` (CTF Config file) and `chall.toml` (Challenge Config file).

In CTF Architect, challenges are stored in a file structure called a Challenge Repository. Each Challenge Repository has a `ctf_config.toml` at the root, which contains metadata about the repository, such as categories, difficulties and flag format.

Meanwhile, a challenge is stored within a subdirectory of the Challenge Repository, and each challenge has a `chall.toml` file which contains metadata about the challenge, such as the flag, hints and services.

The CTF Config file follows the rules of the Challenge Repository Specification, and the Challenge Config file follows the rules of the Challenge Specification.

## The Challenge Repository
The Challenge Repository is a directory that contains all the challenges for a CTF. It has the following structure:

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

The `challenges/` directory contains folders for each challenge category specified in the `ctf_config.toml` file. Each category folder contains the challenges for that category. The `README.md` file in each category folder and the `challenges/` directory contains information such as the difficulty distribution, challenge info, and services.

## Why use CTF Architect?
CTF Architect aims to provide a standardised and streamlined way to manage challenges for a CTF. Unlike alternatives such as [`ctfcli`](https://github.com/CTFd/ctfcli), it is not designed to work with one CTF platform, but rather to be a general-purpose tool for managing challenges.

~~With the ability to create custom extensions and plugins, CTF Architect aims to solely focus on the challenge creation and management aspect of CTFs, leaving the deployment of challenges to plugins and integrations.~~ (NOTE: This is a planned feature, but not yet implemented)

Using CTF Architect has several features to help streamline the development and management of challenges for a CTF:

- **Standardised Format**: All challenges are stored and must be submitted in a standardised format, making it easier to manage and share challenges.
- **Metadata Management**: Metadata for challenges and Challenge Repositories are stored in TOML files, which are easy to read and manually edit.
- **Extensible**: CTF Architect is designed to be extensible, with the ability to add new commands and features easily.
- **Cross-Platform**: CTF Architect tries its best to be platform-independent, with support for Windows and Linux systems.