# Technical Scoring System Migration Guide

This document provides guidance on migrating to the new unified technical scoring system.

## Overview

The technical scoring system has been refactored to address several issues:

1. Duplicate models across multiple files
2. Inconsistent data types and calculations
3. Circular dependencies between models
4. Lack of standardized score calculation

The new system provides:

1. A unified model architecture in `unified_scoring.py`
2. Standardized scoring using `DecimalField`
3. Centralized scoring calculation in `utils/scoring.py`
4. A compatibility layer for transition

## Migration Process

### Step 1: Run Database Migration 

```bash
python manage.py migrate_to_unified_scoring --verbose
```

This command will:
- Create new scoring systems
- Migrate existing scoring criteria
- Set up category configurations
- Migrate performances, scores, and rankings

### Step 2: Update Import Statements

```bash
python manage.py update_scoring_imports --directory competitions/views
```

This will update import statements to use the compatibility layer, allowing for a gradual transition to the new models.

### Compatibility Layer

The compatibility layer in `scoring_compatibility.py` provides:

- Drop-in replacements for old model classes
- Compatibility properties and methods
- Seamless transition between old and new APIs

## Important Files

1. `/competitions/models/unified_scoring.py` - The new unified models
2. `/competitions/utils/scoring.py` - Centralized scoring calculation
3. `/competitions/models/scoring_compatibility.py` - Compatibility layer
4. `/competitions/management/commands/migrate_to_unified_scoring.py` - Migration script
5. `/competitions/management/commands/update_scoring_imports.py` - Import update script

## Troubleshooting

### Common Issues

1. **Import Errors**: If you encounter import errors, check for circular dependencies or incorrect import paths
   - Solution: Use the compatibility layer or fix the import statements

2. **Data Migration Failures**: If data migration fails
   - Solution: Run with `--verbose` flag to see detailed logs and fix specific issues

3. **Model Not Found Errors**: During the transition, you might get model not found errors
   - Solution: Ensure all view files have been updated to use the compatibility layer

### Fixing User Import

If you encounter `ModuleNotFoundError: No module named 'competitions.models.user'`, the import should be updated:

```python
# Incorrect
from competitions.models.user import User

# Correct
from competitions.models.users import User
```

## Future Steps

After successfully migrating to the compatibility layer, gradually update code to directly use the unified models:

1. Replace imports from `scoring_compatibility` with imports from `unified_scoring`
2. Update any model instantiations to use the new model structure
3. Update templates that reference model fields

## Support

If you encounter any issues during migration, consult:

1. Technical scoring system documentation at `/docs/scoring_system.md`
2. Migration logs from the migration command
3. Django debug logs for runtime errors