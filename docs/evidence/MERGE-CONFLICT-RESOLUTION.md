# Merge Conflict Resolution - ENGINEERING-NOTES.md

## Conflict Details

**File**: `ENGINEERING-NOTES.md`  
**PR**: #11 - Merge dev to main  
**Date**: 2024-09-29  
**Branches**: dev → main

## Conflict Description

Both branches modified the same file (`ENGINEERING-NOTES.md`) with different content:

### Dev Branch Version:
- Simple, placeholder answers for questions 1-4
- Brief one-line explanations
- File references only, no detailed implementation notes
- Example: "Factory pattern reads TRIAGE_PROVIDER env var"

### Main Branch Version:
- Comprehensive, detailed answers for all 8 questions
- Complete explanations with code examples
- Specific file paths with line numbers
- Architecture diagrams and flow charts
- References to related ADRs
- Example: Full explanation of runtime config injection with 6+ paragraphs

## Resolution Decision

**Chosen Version**: **Main branch** (detailed version)

### Reasoning:

1. **Completeness**: The main branch version has full, submission-ready documentation with detailed explanations, code snippets, and architecture context. The dev version only had placeholder one-liners.

2. **Submission Requirements**: The assignment requires thorough technical documentation with specific file and line references. The main version provides this; the dev version does not.

3. **Work Quality**: The main branch version represents ~2 hours of documentation work with proper research, while the dev version was a quick placeholder meant to be filled in later.

4. **Consistency**: The main version follows the same detailed format as other documentation files (ADRs, AI-USAGE.md, RUNBOOK.md), maintaining consistency across the project.

5. **References**: The main version includes proper citations (file paths, line numbers, related decisions) that make it useful for onboarding and maintenance.

6. **Educational Value**: The detailed answers in the main version serve as actual engineering notes that explain *how* and *why*, not just *where*.

## Why Not the Dev Version?

The dev branch version was essentially incomplete:
- Questions 1-4 had brief placeholders
- Questions 5-8 were marked as "[Partner to fill in]"
- No code examples or detailed explanations
- Would require complete rewrite to meet submission standards

## Merge Strategy

**Strategy Used**: Accept main branch changes entirely (theirs)

**Command** (if done locally):
```bash
git checkout main -- ENGINEERING-NOTES.md
```

**Or in GitHub UI**:
1. Click "Resolve conflicts"
2. Delete conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. Keep only the main branch content
4. Mark as resolved and commit

## Impact Assessment

### Files Affected:
- `ENGINEERING-NOTES.md` (1 file)

### Code Impact:
- No code changes
- Documentation only
- No breaking changes
- No API modifications

### Risk Level: **Low**
- Documentation merge
- No runtime impact
- No dependency changes

## Lessons Learned

1. **Branching Strategy**: Should have communicated better about who was working on which questions to avoid duplicate work.

2. **Documentation Workflow**: Partner should have pulled latest main before pushing placeholder content to dev.

3. **Early Merges**: Could have merged the detailed version to dev earlier to avoid the conflict.

4. **Division of Labor**: Clear task assignment (Q1-4 vs Q5-8) worked well, but coordination on branch merging needed improvement.

## Screenshots

- `docs/evidence/09-merge-conflict-detected.png` - GitHub showing conflict markers
- `docs/evidence/10-merge-conflict-resolved.png` - After resolution, PR ready to merge

## Related Pull Requests

- **PR #9**: Merge dev to main (included detailed ENGINEERING-NOTES.md)
- **PR #11**: This merge conflict (dev trying to merge older placeholder version)

## Resolution Outcome

✅ **Success**: Main branch version preserved  
✅ **Documentation**: Complete and submission-ready  
✅ **No Data Loss**: Dev version was incomplete anyway  
✅ **Team Agreement**: Both partners agreed detailed version is superior  

---

**Resolved By**: Development Team  
**Date**: 2024-09-29  
**Time**: ~20:18 SGT  
**Method**: GitHub UI conflict resolution
