# Technical Scoring System Documentation

This document outlines the unified technical scoring system architecture for MartialComp.

## Overview

The scoring system is designed to handle various types of technical performances in martial arts competitions, including forms, kata, patterns, and technical demonstrations. It supports different scoring methodologies, weighted criteria, real-time judging, and automated ranking generation.

## Core Components

The scoring system consists of several core components:

1. **Scoring System**: Defines the overall approach to scoring (standard weighted average, point system, direct elimination, custom)
2. **Scoring Criteria**: The specific criteria used to evaluate performances
3. **Category Scoring Configuration**: Links scoring systems to competition categories with optional overrides
4. **Performance**: Represents a practitioner's performance to be scored
5. **Score**: Individual scores from judges for specific criteria
6. **Judge Submission**: Tracks whether judges have submitted all their scores
7. **Competition Ranking**: Final rankings and results

## Data Flow

1. **Setup Phase**:
   - Competition organizers create categories
   - Scoring systems are assigned to categories
   - Criteria are defined for evaluation
   - Judges are assigned to categories

2. **Performance Phase**:
   - Performances are created and scheduled
   - Judges submit scores for each criterion
   - System tracks submission status

3. **Results Phase**:
   - Final scores are calculated
   - Rankings are generated
   - Results are published

## Model Details

### ScoringSystem

Defines the overall approach to scoring in competitions.

Key fields:
- `name`: Name of the scoring system
- `system_type`: Standard (weighted average), Point, Direct Elimination, or Custom
- `min_score`/`max_score`: Score range
- `score_step`: Increment between possible scores
- `exclude_extreme_scores`: Whether to exclude highest and lowest scores
- `allow_ties`: Whether to allow tied rankings
- `real_time_results`: Whether to show results in real-time

### ScoringCriterion

Defines specific criteria for evaluating performances.

Key fields:
- `scoring_system`: The scoring system this criterion belongs to
- `category`: Optional category-specific criterion
- `name`: Name of the criterion (e.g., "Technique", "Balance")
- `weight`: Relative importance of this criterion
- `min_score`/`max_score`: Score range (can inherit from system)
- `step`: Score increment (can inherit from system)

### CategoryScoringConfig

Links a scoring system to a competition category with optional overrides.

Key fields:
- `category`: The competition category
- `scoring_system`: The scoring system to use
- `override_min_score`, `override_max_score`, `override_score_step`: Optional overrides

Methods:
- `get_effective_X()`: Gets the effective configuration values
- `set_default_criteria()`: Creates default criteria based on discipline

### Performance

Represents a participant's performance to be scored.

Key fields:
- `competition`/`category`: Where this performance belongs
- `practitioner`: The performer
- `round_type`/`round_number`: Identifies the competition round
- `performance_order`: Order within the round
- `status`: Pending, In Progress, Completed, Disqualified, or Cancelled
- `start_time`/`end_time`/`duration`: Timing information

Methods:
- `start_performance()`: Mark as in progress
- `end_performance()`: Mark as completed
- `disqualify()`/`cancel()`: Special status changes
- `calculate_final_score()`: Calculate the final score

### Score

Individual scores from judges for specific criteria.

Key fields:
- `performance`: The performance being scored
- `judge`: The judge giving the score
- `criterion`: The criterion being evaluated
- `value`: The score value
- `original_value`: Original score if modified
- `is_locked`: Whether the score can be changed
- `is_training_score`: For training/testing judges

Methods:
- `lock()`: Prevent further changes

### JudgeSubmission

Tracks whether a judge has submitted all scores for a performance.

Key fields:
- `performance`: The performance being judged
- `judge`: The judge
- `is_submitted`: Whether all scores have been submitted
- `submitted_at`: When the submission was completed

Methods:
- `submit()`: Mark as submitted and lock all scores

### CompetitionRanking

Final ranking of competitors in a category.

Key fields:
- `competition`/`category`: Where this ranking belongs
- `practitioner`: The participant
- `performance`: The related performance
- `rank`: Position in the ranking
- `final_score`: Calculated final score
- `is_tie`: Whether tied with another competitor
- `medal`: Gold, Silver, Bronze, or None

### CategoryRankingSnapshot

A snapshot of rankings at a point in time.

Key fields:
- `category`/`competition`: Where this snapshot belongs
- `is_published`: Whether publicly visible
- `is_final`: Whether officially finalized

Methods:
- `publish()`: Make publicly visible
- `finalize()`: Mark as official final results
- `create_from_current_rankings()`: Create a new snapshot

## Utilities

### ScoreCalculator

Centralizes score calculation logic.

Methods:
- `calculate_final_score()`: Calculate the final score based on system type
- `_calculate_standard_score()`: Weighted average calculation
- `_calculate_point_score()`: Point system calculation
- `_calculate_direct_elimination_score()`: Direct elimination scoring
- `_calculate_custom_score()`: Custom scoring implementation

### RankingGenerator

Generates rankings from performance scores.

Methods:
- `generate_rankings()`: Create rankings based on scores
- `handle_third_place_tie()`: Special handling for third place ties
- `create_snapshot()`: Create a snapshot of current rankings

## Usage Examples

### Setting up a scoring system

```python
# Create a scoring system
system = ScoringSystem.objects.create(
    name="International Forms Scoring",
    system_type=ScoringSystem.STANDARD,
    min_score=0.0,
    max_score=10.0,
    score_step=0.1,
    exclude_extreme_scores=True
)

# Create criteria
criterion1 = ScoringCriterion.objects.create(
    scoring_system=system,
    name="Technical Execution",
    weight=1.2,
    order=1
)

criterion2 = ScoringCriterion.objects.create(
    scoring_system=system,
    name="Power",
    weight=0.8,
    order=2
)

# Assign to category
config = CategoryScoringConfig.objects.create(
    category=category,
    scoring_system=system
)

# Set up default criteria
config.set_default_criteria()
```

### Recording scores

```python
# Create a performance
performance = Performance.objects.create(
    competition=competition,
    category=category,
    practitioner=practitioner,
    round_type=Performance.FINAL
)

# Start the performance
performance.start_performance()

# Record a score
score = Score.objects.create(
    performance=performance,
    judge=judge,
    criterion=criterion,
    value=8.5
)

# Mark judge as submitted
submission = JudgeSubmission.objects.get_or_create(
    performance=performance,
    judge=judge
)[0]
submission.submit()  # This also locks all scores

# End the performance
performance.end_performance()
```

### Generating rankings

```python
# Calculate final score
final_score = performance.calculate_final_score()

# Generate rankings for a category
generator = RankingGenerator(category)
rankings = generator.generate_rankings()

# Handle third place ties (if needed)
generator.handle_third_place_tie()

# Create a snapshot of rankings
snapshot = generator.create_snapshot(
    user=current_user,
    name="Final Results",
    publish=True
)
```

## Migration from Old System

A migration command is provided to transition from the older scoring system models to this unified architecture:

```
python manage.py migrate_to_unified_scoring
```

Options:
- `--dry-run`: Run without making actual changes
- `--verbose`: Provide detailed output during migration

## Best Practices

1. **Competition Setup**:
   - Always define clear criteria with appropriate weights
   - Consider discipline-specific scoring needs
   - Test scoring configurations before the competition

2. **Judge Management**:
   - Train judges on the scoring system
   - Ensure consistent understanding of criteria
   - Use training scores for practice

3. **Results Management**:
   - Create snapshots before finalizing results
   - Double-check rankings before publication
   - Handle ties according to competition rules

## Troubleshooting

Common issues and solutions:

1. **Missing Scores**:
   - Check judge submission status
   - Verify judge assignments
   - Ensure all criteria have been scored

2. **Incorrect Rankings**:
   - Verify scoring calculation settings
   - Check for extreme score exclusion
   - Confirm tie-breaking rules

3. **Performance Issues**:
   - Ensure performances have correct status
   - Check start/end times
   - Verify practitioner assignments