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
    │   └── 🐋 compose.yml (local testing only)
    ├── 📁 solution/
    │   └── 📄...
    ├── 📄 chall.yaml
    └── 📄 README.md
```

| File/Directory | Description |
| -------------- | ----------- |
| `src/` | Optional source files for maintainers/testing. |
| `dist/` | Optional distributable files for participants. |
| `services/` | Optional service directories used by `challenge.services[].path`. |
| `solution/` | Optional writeups/solutions for maintainers. |
| `chall.yaml` | YAML metadata for the challenge. |
| `README.md` | Generated challenge summary. |

## Top-level schema

```yaml
version: "0.1"
challenge: { ... }
```

- `version` must be a supported challenge spec version.
- `challenge` must match the `ChallengeConfig` schema below.

## Example `chall.yaml`

```yaml
# Challenge Metadata File (version 0.1)
version: "0.1"

challenge:
  id: "example-challenge"
  name: "Example Challenge"
  description: "This is an example challenge for demonstration purposes."
  category: "web"
  difficulty: "medium"
  author: "example_author"

  # Optional. If omitted, generated from sanitized `name` (fallback `id`).
  folder_name: "Example Challenge"

  # Optional list of challenge IDs.
  requirements:
    - "prereq-challenge-1"
    - "prereq-challenge-2"

  # Optional list of distributable files.
  files:
    - type: "static"
      path: "dist/example.txt"
    - type: "url"
      url: "https://example.com/example.txt"

  # Optional list of accepted flags.
  flags:
    - type: "static"
      value: "flag{example_flag_123}"
      case_sensitive: true
    - type: "regex"
      pattern: "^flag\\{[a-zA-Z0-9_]+\\}$"

  # Optional list of hints.
  hints:
    - cost: 10
      content: "This is a hint"
    - cost: 20
      content: "This hint depends on hint 0"
      requirements:
        - 0

  # Optional free-form primitive labels.
  extra_labels:
    discord: "example#1234"
    finals: true

  # Optional free-form metadata (plugin/extension use).
  annotations:
    created_at: "2026-03-03T12:00:00Z"
    deployment:
      region: "us-east-1"

  # Optional containerized services.
  services:
    - type: "web"
      name: "example-service"
      path: "services/example-service"
      ports:
        - 8080
      networks:
        - "example-net"
      annotations:
        privileged: true

    - type: "internal"
      name: "bot"
      path: "services/bot"
      # `ports` may be omitted only for internal services.

  # Optional service networks.
  networks:
    example-net:
      internal: false
    example-net-internal:
      internal: true
```

## `challenge` fields

### Required

- `id` (`SlugStr`): unique challenge ID.
- `name` (`str`): challenge name.
- `description` (`str`): challenge description.
- `category` (`str`): automatically lowercased; must match `^[a-zA-Z][a-zA-Z0-9 _-]*$`.
- `difficulty` (`str`): automatically lowercased.
- `author` (`str`): author/owner.

### Optional

- `folder_name` (`str`): must match `^[a-zA-Z0-9][a-zA-Z0-9 _-]*$`.
- `requirements` (`list[SlugStr]`): prerequisite challenge IDs.
- `files` (`list[ChallengeFile]`): distributable files.
- `flags` (`list[ChallengeFlag]`): accepted flag definitions.
- `hints` (`list[ChallengeHint]`): hint definitions.
- `extra_labels` (`dict[str, str | int | float | bool]`): custom primitive labels.
- `annotations` (`dict[str, Any]`): extension/plugin metadata.
- `services` (`list[ChallengeService]`): runtime services.
- `networks` (`dict[SlugStr, ChallengeNetworkConfig]`): network definitions.

## Nested types

### `ChallengeFile`

`files[]` is a discriminated union by `type`:

- Static file:

```yaml
- type: "static"
  path: "dist/file.bin"
```

- URL file:

```yaml
- type: "url"
  url: "https://example.com/file.bin"
```

### `ChallengeFlag`

`flags[]` is a discriminated union by `type`:

- Static flag:

```yaml
- type: "static"
  value: "flag{example}"
  case_sensitive: true
```

- Regex flag:

```yaml
- type: "regex"
  pattern: "^flag\\{.*\\}$"
```

### `ChallengeHint`

```yaml
- cost: 100
  content: "Try checking metadata first."
  requirements:
    - 0
```

### `ChallengeService`

```yaml
- type: "tcp"   # one of: web, tcp, ssh, secret, internal
  name: "backend"
  path: "services/backend"
  ports:
    - 1337
  networks:
    - "backend-net"
  annotations:
    restart: "unless-stopped"
```

- `ports` are required for non-`internal` service types.
- `ports` values must be in range `1..65535`.

### `ChallengeNetworkConfig`

```yaml
backend-net:
  internal: true
```
