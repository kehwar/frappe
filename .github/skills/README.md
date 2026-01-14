# Skills Directory

This directory contains reusable skills that extend capabilities for specific domains and tasks.

## Available Skills

### report-expert

Expert guidance on Frappe reports including report types, structure, creation workflow, and best practices. Use this when you need help with:
- Understanding different report types (Script Report, Query Report, Report Builder, Custom Report)
- Creating standard script reports with proper structure
- Working with report columns, filters, and data formatting
- Implementing advanced features like charts, summaries, and custom actions
- Understanding boilerplate code generation for reports
- Troubleshooting report-related issues

**Location:** `.github/skills/report-expert/`

**Key files:**
- `SKILL.md` - Main skill documentation covering all report types and workflows
- `references/script-report-examples.md` - Complete working examples of various report patterns
- `references/column-fieldtypes.md` - Comprehensive guide to all column fieldtypes
- `references/filter-types.md` - Complete reference for filter configurations
- `references/advanced-features.md` - Charts, summaries, custom buttons, and optimization

### frappe-ci-expert

Expert guidance for setting up CI/CD tests for Frappe apps using GitHub Actions. Use this when you need help with:
- Setting up GitHub Actions workflows for Frappe apps
- Configuring database services (MariaDB, PostgreSQL) for CI
- Bench initialization and site creation in CI environments
- Running server tests, UI tests, or parallel tests
- Troubleshooting CI failures

**Location:** `.github/skills/frappe-ci-expert/`

**Key files:**
- `SKILL.md` - Main skill documentation and overview
- `references/workflow-templates.md` - Complete workflow YAML examples
- `references/database-services.md` - Database service configurations
- `references/ci-setup-process.md` - Detailed setup steps explanation
- `references/helper-scripts.md` - Script templates and explanations
- `references/test-execution.md` - Test running strategies
- `references/ci-patterns.md` - Best practices and patterns

### doctype-schema-expert

Expert guidance on Frappe DocType schemas including JSON structure, field types, properties, naming conventions, and best practices. Use this when you need help with:
- Creating or modifying DocType JSON files
- Understanding DocType structure and properties
- Working with field definitions and field types
- Configuring DocType properties and permissions
- Troubleshooting schema-related issues

**Location:** `.github/skills/doctype-schema-expert/`

**Key files:**
- `SKILL.md` - Main skill documentation
- `references/field-types.md` - Complete field type reference
- `references/field-properties.md` - Field property configurations
- `references/doctype-structure.md` - DocType JSON structure guide
- `references/naming-conventions.md` - Naming best practices
- `references/common-patterns.md` - Common DocType patterns
- `references/best-practices.md` - DocType development best practices

### bench-commands

Comprehensive reference for Frappe bench CLI commands. Use this when you need help with:
- Site management and operations
- App installation and updates
- Database operations and migrations
- Backup and restore procedures
- Development workflows and debugging
- Common bench utilities

**Location:** `.github/skills/bench-commands/`

**Key files:**
- `SKILL.md` - Main command reference
- `references/` - Detailed command documentation by category

### skill-creator

The skill-creator provides comprehensive guidance for creating effective skills. Use this when you want to create a new skill or update an existing skill that extends capabilities with specialized knowledge, workflows, or tool integrations.

**Location:** `.github/skills/skill-creator/`

**Key files:**
- `SKILL.md` - Complete skill documentation and instructions
- `scripts/init_skill.py` - Initialize a new skill from template
- `scripts/package_skill.py` - Package a skill into distributable .skill file
- `scripts/quick_validate.py` - Validate skill structure and frontmatter
- `references/workflows.md` - Best practices for workflow patterns
- `references/output-patterns.md` - Best practices for output formatting

**Quick start:**

```bash
# Navigate to the skills directory
cd .github/skills

# Create a new skill
/workspace/development/frappe-bench/env/bin/python skill-creator/scripts/init_skill.py my-new-skill --path .

# Validate a skill
/workspace/development/frappe-bench/env/bin/python skill-creator/scripts/quick_validate.py ./my-new-skill

# Package a skill
/workspace/development/frappe-bench/env/bin/python skill-creator/scripts/package_skill.py ./my-new-skill
```

**Note:** Use the bench virtual environment Python (`/workspace/development/frappe-bench/env/bin/python`) to ensure all dependencies are available.

For complete documentation, see `skill-creator/SKILL.md`.

## Adding New Skills

1. Use the skill-creator to initialize new skills
2. Place skill directories directly in the `.github/skills/` folder
3. Each skill should be self-contained with its own SKILL.md file
4. Follow the patterns documented in skill-creator

## License

Skills are licensed under Apache License 2.0 unless otherwise specified. See individual skill LICENSE.txt files for details.
