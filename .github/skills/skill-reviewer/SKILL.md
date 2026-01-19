---
name: skill-reviewer
description: Review and validate existing skills to ensure they reflect current code, fix inconsistencies, and maintain quality. Use when auditing skills, checking for outdated information, validating skill accuracy against codebase, or creating skill review checklists.
---

# Skill Reviewer

This skill provides guidance for reviewing and validating existing skills to ensure they remain accurate and up-to-date.

## Overview

Skills require regular review to ensure they:
- Reflect current code structure and APIs
- Contain accurate examples and references
- Follow skill creation best practices
- Remain relevant to user workflows
- Don't contain outdated or conflicting information

## Review Process

### 1. Initialize Skills Review

Run the bundled script to generate the skills inventory:

```bash
cd /workspace/development/frappe-bench/apps/frappe
python .github/skills/skill-reviewer/scripts/generate_skills_review.py
```

This creates `docs/skills-review/skills.yaml` with all discovered skills in the current app.

### 2. Enable Skills for Review

Edit `docs/skills-review/skills.yaml` to enable specific skills:

```yaml
skills:
  - name: assignments-expert
    path: .github/skills/assignments-expert/SKILL.md
    enabled: true  # Set to true to include in review

  - name: workflow-expert
    path: .github/skills/workflow-expert/SKILL.md
    enabled: false  # Skip this skill
```

### 3. Generate Review Checklists

Run the review generator to create individual review files:

```bash
python .github/skills/skill-reviewer/scripts/generate_skills_review.py --create-reviews
```

This creates `docs/skills-review/<skill-name>.md` for each enabled skill.

### 4. Review Each Skill

Work through each review file systematically, checking off items as you validate them.

## Review Checklist Items

Each generated review file includes these checks:

### Code Accuracy
- [ ] All code examples are syntactically correct
- [ ] APIs and functions referenced still exist
- [ ] File paths and module imports are accurate
- [ ] DocType names and field references are current
- [ ] Database queries and ORM usage are valid

### Documentation Quality
- [ ] Description accurately reflects skill purpose
- [ ] Examples demonstrate real-world usage
- [ ] No deprecated features or patterns
- [ ] Links to referenced files are valid
- [ ] Prerequisites and dependencies are listed

### Consistency
- [ ] Follows current skill-creator guidelines
- [ ] Consistent with related skills
- [ ] No conflicting information
- [ ] Terminology matches framework conventions
- [ ] Formatting follows markdown best practices

### Completeness
- [ ] Covers the stated domain adequately
- [ ] Includes error handling patterns
- [ ] Shows both simple and complex cases
- [ ] References related skills where appropriate
- [ ] Includes troubleshooting guidance

### Relevance
- [ ] Addresses current user needs
- [ ] Examples use recent framework versions
- [ ] No outdated workarounds
- [ ] Aligns with framework direction

## Review Commands

When reviewing skills, use these commands:

### Scan for Referenced Files

```bash
# Extract file paths mentioned in a skill
grep -oE '`[^`]+\.(py|js|json|md)`' .github/skills/skill-name/SKILL.md

# Check if referenced files exist
while read file; do
    [ -f "$file" ] && echo "✓ $file" || echo "✗ $file (missing)"
done < file_list.txt
```

### Validate Code Blocks

```bash
# Extract Python code blocks from skill
awk '/```python/,/```/' .github/skills/skill-name/SKILL.md > /tmp/skill_code.py

# Check syntax (won't catch runtime errors)
python -m py_compile /tmp/skill_code.py
```

### Check for Outdated Patterns

```bash
# Search for deprecated APIs
grep -n "whitelist\|whitelisted" .github/skills/*/SKILL.md
grep -n "get_list.*ignore_permissions.*1" .github/skills/*/SKILL.md
```

### Cross-Reference Related Files

```python
# Use this to find actual implementation referenced in skill
import frappe
from frappe.utils import get_bench_path
import os

def find_implementation(module_path):
    """Locate the actual file for a module path"""
    bench_path = get_bench_path()
    # Convert module.path to file/path.py
    file_path = module_path.replace(".", "/") + ".py"

    for app in ["frappe", "erpnext", "soldamundo", "tweaks"]:
        full_path = os.path.join(bench_path, "apps", app, file_path)
        if os.path.exists(full_path):
            return full_path
    return None
```

## Common Issues to Check

### Deprecated APIs

Look for these patterns that may be outdated:

```python
# Old whitelist decorator (pre-v14)
@frappe.whitelist()

# Should be (v14+)
@frappe.whitelist()
# (Still valid, but check if allow_guest should be explicit)

# Old permission check
frappe.has_permission(doctype, "read", throw=True)

# May need update based on context
```

### Broken References

- **File paths**: Check if files moved or renamed
- **DocType names**: Verify DocTypes still exist
- **Field names**: Confirm field names haven't changed
- **Hook names**: Validate hooks are still supported
- **Method signatures**: Check if parameters changed

### Incomplete Information

- Missing error handling examples
- No mention of required permissions
- Undocumented side effects
- Missing transaction/commit guidance
- No performance considerations

## Validation Tools

### Automated Checks

Create helper scripts for common validations:

```python
# scripts/validate_skill_references.py
import os
import re
import yaml

def extract_code_references(skill_path):
    """Extract all code references from a skill file"""
    with open(skill_path) as f:
        content = f.read()

    # Find all backtick-wrapped references
    refs = re.findall(r'`([^`]+)`', content)

    # Find file paths
    file_refs = [r for r in refs if '/' in r or r.endswith(('.py', '.js', '.json'))]

    # Find module/function references
    code_refs = [r for r in refs if '.' in r and not r.endswith(('.py', '.js'))]

    return {
        'file_references': file_refs,
        'code_references': code_refs
    }

def validate_file_exists(path, app_name):
    """Check if a referenced file exists in the app"""
    base = f'/workspace/development/frappe-bench/apps/{app_name}'
    full_path = os.path.join(base, path.lstrip('/'))
    return os.path.exists(full_path)
```

### Manual Review Protocol

For each skill:

1. **Read through completely** - Understand the domain and purpose
2. **Test examples** - Copy code blocks and verify they work
3. **Check references** - Validate all file paths and module references
4. **Compare with code** - Review actual implementation files
5. **Update as needed** - Fix issues and enhance clarity
6. **Mark complete** - Check off review items in the review file

## Review File Format

Generated review files follow this structure:

```markdown
# Skill Review: skill-name

**Skill Path**: `.github/skills/skill-name/SKILL.md`
**App**: frappe
**Review Date**: 2026-01-19

## Review Checklist

### Code Accuracy
- [ ] All code examples are syntactically correct
- [ ] APIs and functions referenced still exist
...

## Referenced Files

Check that these files still exist and match the skill's description:

- [ ] `frappe/desk/form/assign_to.py` - Core assignment API
- [ ] `frappe/automation/doctype/assignment_rule/assignment_rule.py` - Assignment Rules
...

## Notes

<!-- Add review notes here -->

## Action Items

- [ ] Update example to use current API
- [ ] Fix broken reference to moved file
...

## Sign-off

- [ ] Review completed by: ___________
- [ ] Changes committed: Yes/No
- [ ] Date: ___________
```

## Best Practices

### Efficient Review

- **Batch similar skills**: Review related skills together for consistency
- **Use automation**: Validate file references and syntax programmatically
- **Test in context**: Run examples in actual bench environment
- **Document changes**: Note what was fixed in commit messages

### Maintaining Quality

- **Regular cadence**: Review skills quarterly or after major framework updates
- **Track changes**: Monitor framework changelog for breaking changes
- **User feedback**: Incorporate issues users report about skills
- **Version awareness**: Tag skills with framework version compatibility

### Collaboration

- **Assign reviews**: Different team members review different skill domains
- **Peer review**: Have changes reviewed before committing
- **Share findings**: Document common issues for future reviews
- **Update templates**: Improve review checklist based on recurring issues

## Scripts Reference

### generate_skills_review.py

Located at `scripts/generate_skills_review.py` within this skill directory.

**Purpose**: Scan current app for skills and generate review infrastructure

**Usage**:
```bash
# Generate skills.yaml inventory
python .github/skills/skill-reviewer/scripts/generate_skills_review.py

# Generate review files for enabled skills
python .github/skills/skill-reviewer/scripts/generate_skills_review.py --create-reviews

# Force regenerate all review files
python .github/skills/skill-reviewer/scripts/generate_skills_review.py --create-reviews --force
```

**Output**:
- `docs/skills-review/skills.yaml` - Inventory of all skills in current app
- `docs/skills-review/<skill-name>.md` - Individual review checklists

The script automatically scans `.github/skills/*/SKILL.md` in the current app directory.

## Workflow Example

```bash
# 1. Initialize review system
cd /workspace/development/frappe-bench/apps/frappe
python .github/skills/skill-reviewer/scripts/generate_skills_review.py

# 2. Edit docs/skills-review/skills.yaml
# Set enabled: true for skills to review

# 3. Generate review files
python .github/skills/skill-reviewer/scripts/generate_skills_review.py --create-reviews

# 4. Review each skill
cd docs/skills-review
ls *.md

# 5. Open a review file
vim assignments-expert.md

# 6. Work through checklist, make updates to skill as needed

# 7. Commit changes
git add .github/skills/assignments-expert/
git add docs/skills-review/assignments-expert.md
git commit -m "Review and update assignments-expert skill"
```

## Integration with Development

### Pre-commit Hooks

Consider adding skill validation to pre-commit:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: validate-skills
      name: Validate skill references
      entry: python scripts/validate_skill_references.py
      language: python
      pass_filenames: false
      files: \.github/skills/.*/SKILL\.md$
```

### CI/CD Integration

Add skill validation to CI pipeline:

```yaml
# .github/workflows/validate-skills.yml
name: Validate Skills
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate skill references
        run: python scripts/validate_skill_references.py
```

## Troubleshooting

### Skills Not Detected

- Check `.github/skills/*/SKILL.md` path convention
- Verify YAML frontmatter is valid
- Ensure markdown file is named exactly `SKILL.md`

### Review Files Not Generated

- Check `skills.yaml` has `enabled: true`
- Verify `docs/skills-review/` directory exists
- Run with `--force` flag to overwrite existing

### Validation Failures

- Review error messages for specific issues
- Check if referenced files use absolute vs relative paths
- Verify app names match actual app directory names

## Summary

The skill review process ensures skills remain accurate, relevant, and valuable. Use the provided scripts to systematically inventory and review skills, following the checklist to validate code accuracy, documentation quality, and overall relevance.

**Key takeaways**:
- Generate `skills.yaml` inventory with `generate_skills_review.py`
- Enable specific skills for review
- Create review files with `--create-reviews` flag
- Work through checklist systematically
- Update skills and commit changes
- Repeat regularly to maintain quality
