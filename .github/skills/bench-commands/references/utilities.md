# Utilities

## Configuration Management

### Set Configuration Value
```bash
bench --site development.localhost set-config key value
```

Sets a configuration value in site_config.json.

**Examples:**
```bash
# Enable developer mode
bench --site development.localhost set-config developer_mode 1

# Set encryption key
bench --site development.localhost set-config encryption_key "your-key-here"

# Set custom config
bench --site development.localhost set-config max_file_size 10485760
```

### Get Configuration Value
```bash
bench --site development.localhost get-config key
```

Retrieves a configuration value.

**Example:**
```bash
bench --site development.localhost get-config developer_mode
```

### View All Configuration
```bash
cat sites/development.localhost/site_config.json
```

Shows complete site configuration file.

## Scheduler Management

### Enable Scheduler
```bash
bench --site development.localhost enable-scheduler
```

Enables background scheduled jobs (hourly, daily, weekly, etc.).

**Scheduled jobs run for:**
- Email sending
- Report generation
- Automated workflows
- Maintenance tasks

### Disable Scheduler
```bash
bench --site development.localhost disable-scheduler
```

Disables scheduled jobs. Useful during development to prevent:
- Unwanted emails
- Background task interference
- Resource consumption

### Check Scheduler Status
```bash
bench --site development.localhost doctor
```

Shows site health including scheduler status.

## DocType Operations

### Reload DocType
```bash
bench --site development.localhost reload-doctype "DocType Name"
```

Reloads a DocType definition from its JSON file.

**Use when:**
- JSON changes not reflecting
- DocType appears corrupted
- After manual JSON edits

### Rebuild DocType
```bash
bench --site development.localhost rebuild-doctype "DocType Name"
```

Completely rebuilds a DocType including database schema.

**Warning:** More aggressive than reload. Use carefully.

## Password Management

### Reset Admin Password
```bash
bench --site development.localhost set-admin-password admin
```

Resets Administrator user password to "admin".

**Use when:**
- Forgot admin password
- After restoring backup
- Initial setup

### Set User Password
```bash
bench --site development.localhost execute "frappe.db.set_value('User', 'user@example.com', 'new_password', 'yourpassword')"
```

Sets password for specific user via console.

## Version Information

### Check Bench Version
```bash
bench --version
```

Shows bench utility version.

### Check Frappe Version
```bash
bench version
```

Shows version of all installed apps.

**Output example:**
```
erpnext 15.0.0
frappe 15.0.0
soldamundo 1.0.0
tweaks 1.0.0
```

### Check App Version
```bash
cd apps/soldamundo && git describe --tags
```

Shows git tag/version for specific app.

## Update Operations

### Update Specific App
```bash
bench update --apps soldamundo
```

Pulls latest code and runs migrations for the specified app.

**Steps performed:**
1. Git pull latest code
2. Install dependencies (requirements.txt, package.json)
3. Run migrations
4. Build assets

### Update All Apps
```bash
bench update
```

Updates all apps in bench.

**Warning:** Can break things. Test in development first.

### Pull Without Migrate
```bash
bench update --pull
```

Only pulls code without running migrations.

**Use when:**
- Want to review changes first
- Manually control migration timing
- Debugging issues

### Update Bench
```bash
bench update --bench
```

Updates the bench tool itself.

## Maintenance Operations

### Clear Website Cache
```bash
bench --site development.localhost clear-website-cache
```

Clears website/portal cache specifically.

### Clear Global Search
```bash
bench --site development.localhost build-search-index
```

Rebuilds the global search index.

**Use when:**
- Search not finding documents
- After bulk data import
- Search results stale

### Optimize Tables
```bash
bench --site development.localhost mariadb
```

Then in MariaDB:
```sql
OPTIMIZE TABLE `tabDocType`;
```

Optimizes database table performance.

## Permission Management

### Setup Requirements
```bash
bench setup requirements
```

Reinstalls Python dependencies from requirements.txt files.

**Use when:**
- Python packages not found
- After requirements.txt changes
- Fixing dependency issues

### Setup SocketIO
```bash
bench setup socketio
```

Reinstalls SocketIO dependencies.

**Use when:**
- Real-time updates not working
- SocketIO connection errors

## Node.js Dependencies

### Install Node Dependencies
```bash
cd apps/soldamundo && yarn install
cd apps/frappe && yarn install
```

Installs/updates JavaScript dependencies.

**Use when:**
- After package.json changes
- Build errors
- Missing JavaScript packages

### Clean Install
```bash
cd apps/soldamundo
rm -rf node_modules
yarn install
```

Complete clean reinstall of node_modules.

## Bench Doctor

### Run Diagnostics
```bash
bench --site development.localhost doctor
```

Runs comprehensive health check on site.

**Checks:**
- Database connectivity
- File permissions
- Scheduler status
- Memory usage
- Port availability

**Output includes:**
- Site configuration
- Installed apps
- Database size
- Error logs

## Helpful Shortcuts

### List All Sites
```bash
bench --site all list
```

Shows all sites in the bench.

### Switch Branch
```bash
cd apps/soldamundo
git checkout develop
cd ../..
bench update --apps soldamundo
```

Switches app to different branch and updates.

### Backup Before Risky Operation
```bash
bench --site development.localhost backup --backup-path "backups/before-risky-change"
# ... perform risky operation ...
```

Always backup before potentially destructive operations.
