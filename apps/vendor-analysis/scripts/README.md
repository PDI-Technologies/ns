# Bootstrap Scripts

## bootstrap.py

Idempotent provisioning script for vendor-analysis application.

### Features

- **100% Idempotent** - Safe to run multiple times
- **Fail-Fast** - Stops on first error with clear messages
- **Live Output** - Streams subprocess output to console
- **Dual Logging** - Console (colored) + bootstrap.log file
- **No Error Swallowing** - All errors and warnings visible

### What It Does

1. Checks Python 3.12+ is installed
2. Checks/installs UV package manager
3. Verifies correct directory
4. Installs/updates dependencies with `uv sync`
5. Validates configuration files (config.yaml, .env)
6. Checks database connectivity
7. Initializes database schema (creates tables)
8. Verifies CLI is working

### Usage

```bash
cd apps/vendor-analysis

# Run bootstrap
python3 scripts/bootstrap.py

# Or make executable and run directly
chmod +x scripts/bootstrap.py
./scripts/bootstrap.py
```

### Requirements

- Python 3.12+
- Rich library for console output (pip install rich)

### Logs

All output is logged to `bootstrap.log` in the directory where you run the script.

### Error Handling

The script follows fail-fast discipline:
- Exits immediately on errors
- Shows clear error messages
- Points to bootstrap.log for details
- No try/catch swallowing
- Subprocess errors propagated with full output

### Idempotency

Safe to run multiple times:
- Skips already-installed UV
- Updates existing virtual environment
- Re-validates configuration
- Re-initializes database (SQLAlchemy create_all is idempotent)
- Checks existing setup before proceeding

### Example Output

```
╭──────────────────────────────────────────────────╮
│     Vendor Analysis Bootstrap                    │
│  Idempotent setup for NetSuite vendor analysis   │
╰──────────────────────────────────────────────────╯

Logging to: bootstrap.log

✓ Python 3.12.4
✓ UV installed: uv 0.4.0
✓ Directory: /opt/ns/apps/vendor-analysis
Installing dependencies...
  Resolved 39 packages in 200ms
  Installed 35 packages
✓ Dependencies installed
✓ config.yaml found
✓ .env found
✓ Database connected: PostgreSQL 17.6
Initializing database schema...
✓ Database schema initialized
✓ CLI working

════════════════════════════════════════════════════

╭──────────────────────────────────────────────────╮
│          ✓ Bootstrap Complete!                   │
│                                                  │
│ Next steps:                                      │
│ 1. Verify NetSuite credentials in .env          │
│ 2. Run: uv run vendor-analysis sync             │
│ 3. Run: uv run vendor-analysis analyze          │
╰──────────────────────────────────────────────────╯
```

### Troubleshooting

**Database not accessible:**
- Script will show database setup options
- Run database setup command
- Re-run bootstrap script

**.env file missing:**
- Script fails with clear message
- Copy from .env.example
- Or symlink from parent: `ln -s ../../.env .env`

**UV installation fails:**
- Manually install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Re-run bootstrap

**Check logs:**
- All details in `bootstrap.log`
- Includes subprocess output
- Includes timestamps and levels
