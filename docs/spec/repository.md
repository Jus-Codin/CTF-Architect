# Challenge Repository Specification v0.1

## Repository Structure

```
.
└── 📁 {repo_name}/
    ├── 📁 challenges/
    │   ├── 📁 {category_name}/
    │   │   ├── 📁 ...
    │   │   └── 📄 README.md
    │   ├── 📁 ...
    │   └── 📄 README.md
    └── 📄 ctf_config.yaml
```

| File/Directory | Description |
| -------------- | ----------- |
| `challenges/` | Category directories for challenge content. |
| `challenges/{category_name}/` | Challenges for a specific category. |
| `README.md` | Generated summary and stats (repo/category level). |
| `ctf_config.yaml` | YAML repository metadata file. |

## Top-level schema

```yaml
version: "0.1"
config: { ... }
```

- `version` must be a supported CTF config spec version.
- `config` must match the `CTFConfig` schema below.

## Example `ctf_config.yaml`

```yaml
# CTF Repository Metadata File (version 0.1)
version: "0.1"

config:
  name: "Demo CTF"
  flag_format: "flag\\{.*\\}"
  starting_port: 8000

  categories:
    - web
    - crypto
    - pwn
    - re
    - misc
    - forensics
    - osint

  difficulties:
    - easy
    - medium
    - hard

  extra_labels:
    - name: "discord"
      description: "Discord username"
      prompt: "Enter your Discord username"
      type: "string"
      required: true
```

## `config` fields

### Required

- `name` (`str`): display name of the CTF.
- `categories` (`list[str]`): non-empty list; values are normalized to lowercase.
- `difficulties` (`list[str]`): non-empty list; values are normalized to lowercase.

### Optional

- `flag_format` (`str | None`): regex-like format guidance for flags.
- `starting_port` (`int | None`): base port for service assignment workflows.
- `extra_labels` (`list[ExtraLabelConfig] | None`): extra challenge metadata fields.

## `ExtraLabelConfig` fields

Each item in `config.extra_labels` has:

- `name` (`str`): key used in challenge `extra_labels`.
- `description` (`str`): human-readable description.
- `prompt` (`str`): prompt shown in CLI flows.
- `type` (`"string" | "integer" | "float" | "boolean"`): expected primitive type.
- `required` (`bool`): whether challenge authors must provide this label.
