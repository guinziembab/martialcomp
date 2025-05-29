# Standalone Scoring System Guide

## Overview

The standalone scoring system is designed to solve the model conflict issues in the MartialComp application. It provides a complete and independent scoring infrastructure without relying on conflicting models or complex relationships between models.

## Key Features

- **Self-contained**: Does not require importing other models, avoiding circular dependencies
- **Direct ID references**: Uses direct ID references instead of ForeignKey relationships for most external models
- **Flexible scoring methods**: Supports weighted average, point-based, and direct elimination scoring
- **Performance tracking**: Tracks participants' performances with timing and status
- **Judge workflow**: Manages the judging process, submission status, and judge UI preferences
- **Results management**: Generates rankings, handles ties, and tracks medals

## Model Structure

### Core Models

1. **StandaloneScoringSystem**
   - Defines a scoring system with configuration options
   - Supports multiple scoring types: standard, point-based, direct elimination, etc.
   - Configurable score ranges, tie handling, real-time results

2. **StandaloneScoringCriterion**
   - Defines individual criteria for a scoring system
   - Configurable weights, score ranges, and order
   - Can be linked to specific categories or available globally

3. **StandaloneCategoryScoringConfig**
   - Links a scoring system to a competition category
   - Provides category-specific overrides for system settings
   - Uses direct ID reference to categories

### Performance and Scoring Models

4. **StandalonePerformance**
   - Represents a participant's performance to be scored
   - Tracks timing, status, and round information
   - Uses direct ID references to competition, category, and practitioner

5. **StandaloneScore**
   - Individual scores from judges for a performance
   - Links criteria, judge, and performance
   - Tracks original and modified values, locking status

6. **StandaloneJudgeSubmission**
   - Tracks whether a judge has submitted all scores for a performance
   - Manages submission timing and status
   - Locks scores when submitted

### Settings and Results Models

7. **StandaloneJudgeSettings**
   - Stores judge UI preferences
   - Configurable display modes, themes, and notification settings
   - Uses direct ID reference to users

8. **StandaloneCompetitionRanking**
   - Final ranking of competitors in a category
   - Tracks rank, score, tie status, and medals
   - Uses direct ID references to competition, category, and practitioner

9. **StandaloneCategoryRankingSnapshot**
   - Represents a complete snapshot of rankings at a point in time
   - Supports draft, published, and final status
   - Useful for preserving historical results

10. **StandaloneRankingSnapshotEntry**
    - Individual entries in a ranking snapshot
    - Stores rank, score, tie status, and medal for each practitioner
    - Links to a ranking snapshot

## Calculation Utilities

The `StandaloneScoreCalculator` utility class provides methods for calculating scores without requiring model imports:

- `calculate_weighted_average()`: Calculate weighted average scores from multiple criteria
- `calculate_point_score()`: Calculate point-based scores (simple sum of all scores)
- `generate_rankings()`: Generate rankings from a list of performance scores
- `handle_third_place_tie()`: Special handling for ties in third place (multiple bronze medals)

## Usage Examples

### Initialize the Scoring System

```python
from competitions.management.commands.init_standalone_scoring import Command
command = Command()
command.handle(verbose=True)
```

### Create a Custom Scoring System

```python
from competitions.models.standalone_scoring import StandaloneScoringSystem, StandaloneScoringCriterion

# Create a scoring system
system = StandaloneScoringSystem.objects.create(
    name="Technical Forms Scoring",
    description="Scoring system for technical forms competitions",
    system_type=StandaloneScoringSystem.STANDARD,
    min_score=0.0,
    max_score=10.0,
    score_step=0.1,
    exclude_extreme_scores=True,
    allow_ties=True,
    real_time_results=True,
)

# Add criteria
StandaloneScoringCriterion.objects.create(
    scoring_system=system,
    name="Technical Execution",
    description="Correctness of techniques",
    weight=1.2,
    order=1,
    is_active=True,
)
```

### Calculate Scores

```python
from competitions.utils.standalone_scoring import StandaloneScoreCalculator

# Initialize calculator
calculator = StandaloneScoreCalculator(
    min_score=0.0,
    max_score=10.0,
    exclude_extreme_scores=True
)

# Prepare score data
scores = [
    {
        'criterion_id': 1,
        'criterion_name': 'Technical Execution',
        'criterion_weight': 1.2,
        'judge_scores': [8.5, 9.0, 8.7, 9.2, 8.8]
    },
    {
        'criterion_id': 2,
        'criterion_name': 'Power',
        'criterion_weight': 0.8,
        'judge_scores': [9.0, 8.5, 9.2, 8.8, 9.1]
    }
]

# Calculate weighted average
result = calculator.calculate_weighted_average(scores)
print(f"Final score: {result['final_score']}")
```

### Generate Rankings

```python
from competitions.utils.standalone_scoring import StandaloneScoreCalculator

calculator = StandaloneScoreCalculator()

performances = [
    {'performance_id': 1, 'practitioner_id': 101, 'final_score': 9.25},
    {'performance_id': 2, 'practitioner_id': 102, 'final_score': 9.45},
    {'performance_id': 3, 'practitioner_id': 103, 'final_score': 9.10},
    {'performance_id': 4, 'practitioner_id': 104, 'final_score': 9.45}  # Tie with ID 102
]

rankings = calculator.generate_rankings(performances, allow_ties=True)
for rank in rankings:
    print(f"Practitioner {rank['practitioner_id']}: Rank {rank['rank']}, Score {rank['final_score']}, Medal: {rank['medal']}")
```

## Migration

The system is installed using a direct SQL migration that doesn't require loading any model classes:

```bash
python manage.py migrate competitions 0003_create_standalone_scoring
python manage.py init_standalone_scoring --verbose
```

## Best Practices

1. Always use the calculator utility methods for score calculations to ensure consistency.
2. When creating new performance records, use the provided methods like `start_performance()` and `end_performance()` to maintain proper state.
3. Use the `StandaloneCategoryScoringConfig` to override system settings for specific categories rather than creating separate scoring systems.
4. For judge submissions, use the `submit()` method which will lock all associated scores.
5. Use snapshots when you need to preserve historical ranking data.

## Integration with Views

When integrating with views, avoid importing conflicting models by using direct ID references:

```python
def assign_scores(request, performance_id, judge_id):
    # Get performance by ID
    performance = StandalonePerformance.objects.get(id=performance_id)
    
    # Get category configuration
    config = StandaloneCategoryScoringConfig.objects.filter(
        category_id=performance.category_id
    ).first()
    
    # Get criteria for this scoring system
    criteria = StandaloneScoringCriterion.objects.filter(
        scoring_system=config.scoring_system,
        is_active=True
    ).order_by('order')
    
    # Process form submission
    if request.method == 'POST':
        for criterion in criteria:
            score_value = request.POST.get(f'score_{criterion.id}')
            if score_value:
                StandaloneScore.objects.update_or_create(
                    performance=performance,
                    judge_id=judge_id,
                    criterion=criterion,
                    defaults={'value': score_value}
                )
                
        # Mark as submitted if appropriate
        if 'submit' in request.POST:
            submission, created = StandaloneJudgeSubmission.objects.get_or_create(
                performance=performance,
                judge_id=judge_id
            )
            submission.submit()
    
    # Rest of the view logic...
```