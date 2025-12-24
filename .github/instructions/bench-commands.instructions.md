# Bench Commands Reference

This guide provides commonly used bench commands for development with the `development.localhost` site.

## Environment Constants

- **Site Name**: `development.localhost`
- **Database Root Password**: `123`
- **Admin Password**: `admin`
- **Bench Path**: `/workspace/development/frappe-bench`

## Site Management

### Create a New Site

```bash
bench new-site development.localhost --admin-password admin --db-root-password 123
```

### Drop a Site

```bash
bench drop-site development.localhost --db-root-password 123
```

This automatically creates a backup before dropping and moves the site to `archived/sites/`.

### Reinstall a Site (Drop and Recreate)

```bash
bench drop-site development.localhost --db-root-password 123
bench new-site development.localhost --admin-password admin --db-root-password 123
```

## App Management

### Install Apps to Site

```bash
# Install all custom apps
bench --site development.localhost install-app soldamundo
bench --site development.localhost install-app tweaks

# Or install multiple at once
bench --site development.localhost install-app soldamundo tweaks
```

### Uninstall Apps from Site

```bash
bench --site development.localhost uninstall-app tweaks --yes --no-backup
bench --site development.localhost uninstall-app soldamundo --yes --no-backup
```

### Get New App from Repository

```bash
bench get-app https://github.com/kehwar/frappe_soldamundo.git
bench get-app https://github.com/kehwar/frappe_tweaks.git
```

## Backup and Restore

### Create Backup

```bash
# Full backup (database + files)
bench --site development.localhost backup --backup-path "backups"

# Database only
bench --site development.localhost backup --only-db --backup-path "backups"

# With custom backup path
bench --site development.localhost backup --backup-path "/path/to/backups"
```

### Restore from Backup

```bash
# Restore database and files
bench --site development.localhost restore \
    --db-root-password 123 \
    "backups/20251224_151238-gruposoldamundo_frappe_cloud-database.sql.gz" \
    --with-public-files "backups/20251224_151238-gruposoldamundo_frappe_cloud-files.tar"

# Restore database only
bench --site development.localhost restore \
    --db-root-password 123 \
    "backups/backup-database.sql.gz"
```

## Database Operations

### Migrate Database

```bash
# Run all pending migrations
bench --site development.localhost migrate

# Skip search index build (faster)
bench --site development.localhost migrate --skip-search-index
```

### Run Specific Patch

```bash
bench --site development.localhost run-patch --force tweaks.patches.YYYY.patch_name
bench --site development.localhost run-patch --force soldamundo.patches.YYYY.patch_name
```

### Access Database Console

```bash
# MariaDB console (requires existing site)
bench --site development.localhost mariadb

# Direct connection to MariaDB as root
mariadb -h mariadb -u root -p123

# Or with full bench console (Python)
bench --site development.localhost console
```

### Configure MariaDB Runtime Settings

```bash
# Connect to MariaDB as root
mariadb -h mariadb -u root -p123

# Then run SQL commands:
# Set maximum packet size to 512MB (for large backups/restores)
SET GLOBAL max_allowed_packet=536870912;

# Set InnoDB buffer pool to 6GB (for 8GB total memory allocation)
SET GLOBAL innodb_buffer_pool_size=6442450944;

# View current settings
SHOW VARIABLES LIKE 'max_allowed_packet';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

# Exit MariaDB
EXIT;
```

**Note**: Runtime settings are lost when the MariaDB container restarts. To make them permanent, add them to `/workspace/.devcontainer/docker-compose.yml` under the `mariadb` service's `command` section.

## Development Server

### Start Development Server

```bash
# Start all services (web, socketio, schedule, worker)
bench start

# Start in background
bench start &
```

### Stop Development Server

```bash
# If running in foreground: Ctrl+C

# If running in background or stuck processes
pkill -SIGINT -f bench
pkill -SIGINT -f socketio

# Or use the VS Code task
# Task: "Clean Honcho SocketIO Watch Schedule Worker"
```

## Build and Assets

### Build Assets

```bash
# Build all assets for all apps
bench build

# Build for specific app
bench build --app soldamundo

# Clear cache and rebuild
bench clear-cache
bench build
```

### Watch Assets (Development)

```bash
# Watch and rebuild on changes
bench watch

# For frontend development with Nuxt (soldamundo)
cd apps/soldamundo && yarn dev
```

## Code Management

### Clear Cache

```bash
# Clear all caches
bench clear-cache

# Clear specific site cache
bench --site development.localhost clear-cache
```

### Reload Doctype

```bash
bench --site development.localhost reload-doctype "DocType Name"
```

### Set Developer Mode

```bash
bench --site development.localhost set-config developer_mode 1
bench --site development.localhost clear-cache
```

## Testing

### Run Tests

```bash
# Run all tests for an app
bench --site development.localhost run-tests --app soldamundo
bench --site development.localhost run-tests --app tweaks

# Run specific test file
bench --site development.localhost run-tests --module soldamundo.soldamundo.doctype.doctype_name.test_doctype_name

# Run with coverage
bench --site development.localhost run-tests --app soldamundo --coverage
```

## Python Console

### Open Console

```bash
# Interactive Python console with Frappe context
bench --site development.localhost console

# Then in console:
# frappe.get_doc("DocType", "name")
# frappe.db.sql("SELECT * FROM tabUser LIMIT 5")
```

## Utilities

### Execute Python Code

```bash
bench --site development.localhost execute "frappe.db.commit()"
```

### Set Config Value

```bash
bench --site development.localhost set-config key value
```

### Get Config Value

```bash
bench --site development.localhost get-config key
```

### Enable/Disable Scheduler

```bash
bench --site development.localhost enable-scheduler
bench --site development.localhost disable-scheduler
```

## Common Workflows

### Fresh Install Workflow

```bash
# 1. Drop existing site (if exists)
bench drop-site development.localhost --db-root-password 123

# 2. Create new site
bench new-site development.localhost --admin-password admin --db-root-password 123

# 3. Install apps
bench --site development.localhost install-app soldamundo tweaks

# 4. Enable developer mode
bench --site development.localhost set-config developer_mode 1

# 5. Run migrations
bench --site development.localhost migrate

# 6. Clear cache and build
bench clear-cache
bench build

# 7. Start server
bench start
```

### Restore from Production Backup Workflow

```bash
# 1. Drop existing site
bench drop-site development.localhost --db-root-password 123

# 2. Create new site (required for restore)
bench new-site development.localhost --admin-password admin --db-root-password 123

# 3. Restore from backup
bench --site development.localhost restore \
    --db-root-password 123 \
    "backups/production-database.sql.gz" \
    --with-public-files "backups/production-files.tar"

# 4. Run migrations (if apps have changed)
bench --site development.localhost migrate

# 5. Clear cache
bench clear-cache

# 6. Start server
bench start
```

### Quick Reinstall Apps Workflow

```bash
# Uninstall and reinstall without dropping site
bench --site development.localhost uninstall-app soldamundo --yes --no-backup
bench --site development.localhost install-app soldamundo
bench --site development.localhost migrate
bench clear-cache
```

## Troubleshooting

### Fix Permission Issues

```bash
bench setup requirements
bench setup socketio
```

### Fix Node Dependencies

```bash
cd apps/soldamundo && yarn install
cd ../frappe && yarn install
```

### Reset Admin Password

```bash
bench --site development.localhost set-admin-password admin
```

### Check Bench Version

```bash
bench --version
```

### Update Apps

```bash
# Update specific app
bench update --apps soldamundo

# Update all apps
bench update

# Pull without migrate
bench update --pull
```

## Notes

- Always run `bench` commands from the bench directory (`/workspace/development/frappe-bench`)
- Use `--db-root-password 123` for operations requiring database root access
- Backups are automatically created in `./sites/development.localhost/private/backups/` unless specified otherwise
- Developer mode should be enabled for development: `bench --site development.localhost set-config developer_mode 1`
- After code changes, run `bench clear-cache` and `bench build` before restarting
