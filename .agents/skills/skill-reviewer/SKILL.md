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

**CRITICAL**: The review process requires thorough individual assessment of EACH skill file. DO NOT skip files or batch-process without individual validation. Each skill must be independently verified against the codebase.

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

**IMPORTANT**: Even if reviewing multiple skills, each must be individually assessed. Do not make assumptions about one skill based on another.

### 3. Generate Review Checklists

Run the review generator to create individual review files:

```bash
python .github/skills/skill-reviewer/scripts/generate_skills_review.py --create-reviews
```

This creates `docs/skills-review/<skill-name>.md` for each enabled skill.

### 4. Review Each Skill Individually

**MANDATORY APPROACH**: Work through EACH review file independently:

1. **Read the entire skill file** - Do not skim or summarize
2. **Verify each code example** - Actually test the code, don't assume it works
3. **Check every file reference** - Use read_file/file_search to verify each path
4. **Validate all DocType references** - Search the codebase for each mentioned DocType
5. **Test all hook examples** - Verify hooks exist and work as described
6. **Review all workflow descriptions** - Confirm against actual implementation
7. **Check each API reference** - Verify method signatures and parameters

**DO NOT**:
- Skip sections assuming they're correct
- Batch-validate multiple files without individual checks
- Make changes without verifying against actual code
- Assume examples work without testing
- Rely on skill descriptions without code verification

## Review Checklist Items

Each generated review file includes these checks. **IMPORTANT**: Every item must be individually verified - DO NOT check items as complete without actual validation.

### Code Accuracy (VERIFY EACH EXAMPLE)
- [ ] All code examples are syntactically correct - **Test each one individually**
- [ ] APIs and functions referenced still exist - **Search codebase for each reference**
- [ ] File paths and module imports are accurate - **Use read_file to verify each path**
- [ ] DocType names and field references are current - **Check DocType JSON files**
- [ ] Database queries and ORM usage are valid - **Review against actual schema**

### Documentation Quality (READ THOROUGHLY)
- [ ] Description accurately reflects skill purpose - **Compare with actual code behavior**
- [ ] Examples demonstrate real-world usage - **Verify examples match current patterns**
- [ ] No deprecated features or patterns - **Check framework changelog**
- [ ] Links to referenced files are valid - **Open and verify each linked file**
- [ ] Prerequisites and dependencies are listed - **Confirm all dependencies exist**

### Consistency (CROSS-REFERENCE)
- [ ] Follows current skill-creator guidelines - **Review against skill-creator SKILL.md**
- [ ] Consistent with related skills - **Read related skills for conflicts**
- [ ] No conflicting information - **Verify across all skill sections**
- [ ] Terminology matches framework conventions - **Check Frappe documentation**
- [ ] Formatting follows markdown best practices - **Review entire markdown structure**

### Completeness (ASSESS COVERAGE)
- [ ] Covers the stated domain adequately - **Identify gaps through code search**
- [ ] Includes error handling patterns - **Check for try/except examples**
- [ ] Shows both simple and complex cases - **Verify example diversity**
- [ ] References related skills where appropriate - **Search for missing cross-references**
- [ ] Includes troubleshooting guidance - **Validate troubleshooting steps**

### Relevance (VERIFY CURRENCY)
- [ ] Addresses current user needs - **Review recent issues/discussions**
- [ ] Examples use recent framework versions - **Check version compatibility**
- [ ] No outdated workarounds - **Verify solutions are still needed**
- [ ] Aligns with framework direction - **Review roadmap/changelog**

**VALIDATION PROTOCOL**: For EACH checklist item:
1. Read the relevant section of the skill
2. Use tools (read_file, grep_search, semantic_search) to verify against code
3. Test examples where applicable
4. Only check the box after explicit verification
5. Document findings in review notes

## Anti-Patterns: Avoiding Oversimplification

**CRITICAL WARNING**: The following behaviors indicate oversimplified review and MUST be avoided:

### Signs of Oversimplification

❌ **Skipping File Verification**
- Saying "files look good" without using `read_file` on each one
- Assuming file paths are correct based on naming patterns
- Not verifying file content matches skill descriptions

✅ **Proper Approach**: Use `read_file` on EVERY referenced file path. Verify content actually matches what the skill claims.

❌ **Batch Validation**
- Checking multiple code examples together
- Saying "all examples are correct" without individual testing
- Grouping similar references without individual verification

✅ **Proper Approach**: Test EACH code example independently. Verify EACH file reference separately.

❌ **Assumption-Based Review**
- "This skill is similar to X, so it's probably fine"
- "This is a core Frappe feature, it hasn't changed"
- "The author is experienced, they wouldn't make mistakes"

✅ **Proper Approach**: Treat EVERY skill as potentially outdated. Verify EVERYTHING against current code.

❌ **Superficial Reading**
- Skimming the skill instead of reading thoroughly
- Reading only code examples and skipping explanations
- Ignoring sections that seem "less important"

✅ **Proper Approach**: Read the ENTIRE skill word-for-word. Verify EVERY claim made.

❌ **Incomplete Documentation**
- Marking checklist items without notes
- Not recording what was verified
- No evidence of actual verification work

✅ **Proper Approach**: Document EXACTLY what was checked and how. Provide specific file paths, line numbers, and verification methods.

❌ **Speed Over Quality**
- Rushing through multiple skills quickly
- Setting time limits that encourage shortcuts
- Reviewing faster than the recommended minimum times

✅ **Proper Approach**: Take the necessary time. If review seems too fast, it probably is - go deeper.

### Mandatory Verification Steps Per Skill

For EACH skill, you MUST perform these steps individually:

1. **Read entire skill file** (no skipping)
   - Use `read_file` to load the complete SKILL.md
   - Read every section
   - Note every claim, example, and reference

2. **Verify EVERY file path mentioned**
   - Extract all file paths using grep/regex
   - Use `read_file` on EACH path
   - Confirm content matches description
   - Document each file checked

3. **Test EVERY code example**
   - Copy each code block
   - Verify syntax
   - Check against actual codebase
   - Test if example would actually work
   - Document results for each

4. **Check EVERY DocType reference**
   - Find DocType JSON file
   - Read schema
   - Verify field names
   - Check field types
   - Document each DocType checked

5. **Validate EVERY API/function reference**
   - Search codebase for each function
   - Read implementation
   - Verify signature
   - Check parameters match
   - Document each API checked

6. **Cross-check ALL hook examples**
   - Find hook in framework
   - Read hook documentation
   - Verify example matches current usage
   - Test hook signature
   - Document each hook verified

7. **Review ALL workflow descriptions**
   - Find implementation code
   - Trace execution
   - Verify steps are accurate
   - Check for omissions
   - Document flow verified

### Quality Control Questions

Before marking a skill review complete, answer these:

1. **Did you read the entire skill file?** (yes/no)
2. **How many file paths did you verify with read_file?** (specific number)
3. **Which code examples did you test?** (list each one)
4. **What tools did you use for verification?** (list specific tool invocations)
5. **How long did the review take?** (actual time in minutes)
6. **What issues did you find?** (specific list, or "none found" with evidence)
7. **What files did you create/update?** (specific paths)
8. **Can you provide evidence for each checked item?** (yes/no)

If you can't answer all these questions with specifics, the review is incomplete.

### Evidence Requirements

When marking a checklist item complete, you MUST provide:

- **File paths** verified
- **Line numbers** checked
- **Tool commands** used
- **Test results** obtained
- **Specific findings** discovered

Example of PROPER evidence:
```
✓ File paths verified:
  - frappe/desk/form/assign_to.py (lines 1-150) - read_file confirmed
  - frappe/automation/doctype/assignment_rule/assignment_rule.py (lines 1-200) - read_file confirmed
  - Tested assign() function signature matches skill example
  - Verified ToDo creation flow in lines 45-67
```

Example of INSUFFICIENT evidence:
```
✓ All file paths checked and look good
```

**RULE**: If you can't provide specific evidence, the item isn't verified.

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

**CRITICAL REQUIREMENT**: Each skill MUST be reviewed individually with the following rigorous process. DO NOT skip steps or assume correctness.

For each skill file:

1. **Read through completely**
   - Read every word of the skill file
   - Understand the full domain and purpose
   - Take notes on key claims and examples
   - DO NOT skim or summarize without reading

2. **Verify every code example**
   - Copy EACH code block individually
   - Test syntax with appropriate tools
   - Verify against actual codebase
   - Check if imports/modules exist
   - DO NOT assume examples work

3. **Check ALL file references**
   - Use `read_file` on EVERY mentioned file path
   - Verify each file exists at the stated location
   - Confirm file content matches description
   - Update paths if files have moved
   - DO NOT skip any file reference

4. **Validate EVERY DocType reference**
   - Search for each mentioned DocType JSON file
   - Read the DocType schema
   - Verify field names match
   - Check if DocTypes still exist
   - DO NOT assume DocTypes are unchanged

5. **Test ALL hook examples**
   - Find hook registration in hooks.py
   - Read actual hook implementation
   - Verify hook signature matches
   - Check if hook still fires as described
   - DO NOT trust hook examples without verification

6. **Review ALL workflow descriptions**
   - Read actual implementation code
   - Trace execution flow
   - Verify steps match reality
   - Check for missing steps
   - DO NOT accept workflow descriptions at face value

7. **Check EVERY API reference**
   - Find each API method in codebase
   - Verify method signature
   - Check parameter names and types
   - Confirm return values
   - DO NOT skip API verification

8. **Document ALL findings**
   - Note every discrepancy found
   - Record all updates made
   - List files verified
   - Track items needing fixes
   - DO NOT rely on memory

9. **Update skill as needed**
   - Fix ALL issues found
   - Enhance unclear sections
   - Add missing examples
   - Update deprecated patterns
   - DO NOT leave issues unresolved

10. **Mark complete with evidence**
    - Check off review items with verification notes
    - Provide specific evidence for each item
    - List tools used to verify
    - Include file paths checked
    - DO NOT mark complete without evidence

**INDIVIDUAL FILE ASSESSMENT**: When a skill references multiple files (e.g., DocType controller, JSON schema, hooks.py):

1. Read EACH file completely using `read_file`
2. Verify the skill's description matches EACH file's actual content
3. Cross-reference between files for consistency
4. Check that examples use the correct file's APIs
5. Note any missing files that should be mentioned

**TIME REQUIREMENT**: Proper review of a single skill typically requires:
- Simple skills (< 100 lines): 15-30 minutes minimum
- Medium skills (100-300 lines): 30-60 minutes minimum
- Complex skills (> 300 lines): 1-2 hours minimum

If you complete a review faster, you're likely oversimplifying. Go back and verify more thoroughly.

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

### Efficient Yet Thorough Review

**DO**:
- **Review each skill individually** - Complete one skill fully before starting another
- **Use automation wisely** - Automate file existence checks, but manually verify content
- **Test in real environment** - Run examples in actual bench with real data
- **Document everything** - Keep detailed notes of what was verified and how
- **Take breaks** - Thorough review is mentally intensive; avoid fatigue errors
- **Create verification scripts** - Build reusable tools for common checks
- **Cross-reference thoroughly** - Check related skills for consistency, but don't skip steps

**DO NOT**:
- **Batch process skills** - Don't try to review multiple skills simultaneously
- **Trust automated checks alone** - Always verify critical information manually
- **Skip verification steps** - Every file path, every example must be checked
- **Assume similarity** - Don't skip checks because "this skill is like that one"
- **Rush the process** - Quality over speed; thorough review prevents bugs
- **Skip testing examples** - Always test code examples, don't assume they work
- **Overlook edge cases** - Check that skills cover error scenarios

### Maintaining Quality

- **Regular cadence**: Review skills quarterly or after major framework updates
- **Track changes**: Monitor framework changelog for breaking changes affecting skills
- **User feedback**: Incorporate issues users report about skills - investigate each report individually
- **Version awareness**: Tag skills with framework version compatibility where relevant
- **Individual accountability**: Assign specific skills to reviewers, not skill groups

### Collaboration

- **Assign specific skills**: Give reviewers individual skills to own, not categories
- **Peer review changes**: Have skill updates reviewed file-by-file before committing
- **Share detailed findings**: Document specific issues found, with file paths and line numbers
- **Update templates**: Improve review checklist based on actual issues encountered
- **Knowledge transfer**: When reassigning skills, provide detailed handoff notes

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

The skill review process ensures skills remain accurate, relevant, and valuable through **thorough individual assessment** of each skill file. This is NOT a batch process - each skill requires dedicated, focused review with explicit verification of every claim.

**Core Principles**:
- **Individual Assessment**: Review ONE skill at a time, completely
- **Explicit Verification**: Use tools to verify EVERY file, example, and reference
- **No Assumptions**: Don't assume correctness - verify against actual code
- **Complete Documentation**: Record specific evidence for all verifications
- **Quality Over Speed**: Thorough review prevents user-facing bugs

**Required Process**:
1. Generate `skills.yaml` inventory with `generate_skills_review.py`
2. Enable ONE or more specific skills for review
3. Create review files with `--create-reviews` flag
4. Review EACH skill file INDIVIDUALLY following the complete protocol:
   - Read entire file
   - Verify every file path with `read_file`
   - Test every code example
   - Check every DocType/API reference
   - Document all findings with evidence
5. Update skills based on verified findings
6. Commit changes with detailed notes
7. Repeat for next skill

**Time Investment**:
- Simple skill: 15-30 minutes minimum
- Medium skill: 30-60 minutes minimum
- Complex skill: 1-2 hours minimum

**Red Flags** (indicating oversimplification):
- ❌ Completing reviews faster than minimum times
- ❌ Checking items without documented evidence
- ❌ "All files look good" without specific verification
- ❌ Skipping file reads or code example testing
- ❌ Batch processing multiple skills simultaneously

**Success Criteria**:
- ✅ Every file path verified with `read_file`
- ✅ Every code example tested
- ✅ Specific evidence documented for each check
- ✅ Issues found and fixed with code references
- ✅ Review time meets minimum requirements
- ✅ Can answer all quality control questions

Remember: **Each skill is independently assessed. No shortcuts, no skipping, no assumptions.**
