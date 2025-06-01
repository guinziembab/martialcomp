# MartialComp Standalone Scoring System

This module provides a standalone scoring system for MartialComp that resolves model conflicts and provides a clean, self-contained implementation.

## Installation

Follow these steps to install and initialize the standalone scoring system:

1. **Fix the migration file**:
   The migration file contains a typo in the table name. The file `0003_create_standalone_scoring_fixed.py` has been created with the correct table names.

   ```bash
   # Rename the old migration file to avoid conflicts
   mv competitions/migrations/0003_create_standalone_scoring.py competitions/migrations/0003_create_standalone_scoring.old
   # Move the fixed file to the correct location
   mv competitions/migrations/0003_create_standalone_scoring_fixed.py competitions/migrations/0003_create_standalone_scoring.py
   ```

2. **Apply the migration**:
   ```bash
   python manage.py migrate competitions 0003_create_standalone_scoring
   ```

3. **Initialize the scoring system with default data**:
   ```bash
   python manage.py init_standalone_scoring --verbose
   ```

## Models

The standalone scoring system includes these key models:

- `StandaloneScoringSystem` - Defines scoring methods and parameters
- `StandaloneScoringCriterion` - Defines criteria for evaluation
- `StandaloneCategoryScoringConfig` - Links categories to scoring systems
- `StandalonePerformance` - Represents a performance to be scored
- `StandaloneScore` - Individual scores from judges
- `StandaloneJudgeSubmission` - Tracks judge submission status
- `StandaloneCompetitionRanking` - Final rankings and results

## Benefits

This implementation solves several problems:

1. **Avoids model conflicts**: 
   - Uses direct ID references instead of model relations for most external models
   - Prevents duplicate model name issues

2. **Self-contained system**:
   - Doesn't require importing other models
   - Eliminates circular dependencies

3. **Clean migration path**:
   - Uses direct SQL migration instead of Django's ORM
   - Bypasses model loading, which was causing conflicts

4. **Flexible scoring**:
   - Supports multiple scoring methods (weighted average, point-based, etc.)
   - Configurable for various competition types

## Usage

For detailed usage instructions, see `/docs/standalone_scoring_guide.md`.

Basic usage examples:

```python
# Create a scoring system
from competitions.models.standalone_scoring import StandaloneScoringSystem
system = StandaloneScoringSystem.objects.create(
    name="Competition Scoring",
    description="Standard scoring for the competition",
    system_type=StandaloneScoringSystem.STANDARD,
    min_score=0.0,
    max_score=10.0,
)

# Calculate scores
from competitions.utils.standalone_scoring import StandaloneScoreCalculator
calculator = StandaloneScoreCalculator()
result = calculator.calculate_weighted_average(scores_data)
```

## Further Development

Future enhancements could include:

1. Admin interface for managing scoring systems
2. API endpoints for mobile applications
3. Reporting tools for competition results
4. Integration with real-time scoring displays

## Troubleshooting

If you encounter issues with the migration:

1. Check the database connection settings
2. Verify that the SQL syntax is compatible with your database engine
3. Try running the migration with `--traceback` for more detailed error information:
   ```bash
   python manage.py migrate competitions 0003_create_standalone_scoring --traceback
   ```

For model errors, check that you're importing from the standalone module:
```python
# Correct import
from competitions.models.standalone_scoring import StandaloneScoringSystem

# Avoid importing conflicting models
# from competitions.models.scoring import ScoringSystem  # Don't do this
```