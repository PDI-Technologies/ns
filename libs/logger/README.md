# libs.logger

Shared logging library with rolling archives and custom formatting.

## Features

- Custom log format with process ID, thread ID, and module name
- Rolling file handler with automatic archiving
- Size-based log rotation
- Fail-fast configuration validation
- Type-safe with Pyright strict mode

## Log Format

```
20251024 142530.123 I 0x00001a2b 0x00007f3c netsuite.client "Fetching vendors from NetSuite"
│                   │ │          │          │                │
│                   │ │          │          │                └─ Log message
│                   │ │          │          └─ Python module name
│                   │ │          └─ Thread ID (hex, 8 char padded)
│                   │ └─ Process ID (hex, 8 char padded)
│                   └─ Level: C|E|W|I|D (single char, no brackets)
└─ Timestamp (YYYYMMDD HHMMSS.mmm)
```

## Configuration

Add to `config.yaml`:

```yaml
logging:
  level: INFO                      # DEBUG|INFO|WARNING|ERROR|CRITICAL (required)
  file_path: logs                  # Directory for active log (required)
  archive_path: logs/archive       # Directory for archives (required)
  max_size_mb: 10                  # Max size before rotation (required)
```

All fields are **required**. Application will fail if any field is missing.

## Usage

```python
import yaml
from libs.logger import get_logger, load_logging_config

# Load config
with open("config.yaml") as f:
    config_dict = yaml.safe_load(f)

# Initialize logger
logging_config = load_logging_config(config_dict)
logger = get_logger("my-app", logging_config)

# Use logger
logger.info("Application started")
logger.error("Something went wrong")
logger.debug("Debug information")
```

## Log Files

- Active log: `{file_path}/{app_name}.log`
- Archived logs: `{archive_path}/{app_name}_YYYYMMDD_HHMMSS.log`
- Up to 10 archived files kept (oldest automatically deleted)

## Development

```bash
# Install dependencies
cd libs/logger
uv sync

# Type checking
uv run pyright

# Linting
uv run ruff check .

# Formatting
uv run ruff format .
```
