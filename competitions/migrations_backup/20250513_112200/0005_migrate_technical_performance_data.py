# Generated manually to migrate data from old models to renamed models

from django.db import migrations

def forward_data_migration(apps, schema_editor):
    """
    Migrate data from original TechnicalPerformance, TechnicalScore, JudgeSubmissionStatus 
    models to the renamed versions.
    """
    # Get model classes
    TechnicalPerformance = apps.get_model('competitions', 'TechnicalPerformance')
    TechnicalPerformanceResult = apps.get_model('competitions', 'TechnicalPerformanceResult')
    
    TechnicalScore = apps.get_model('competitions', 'TechnicalScore')
    TechnicalScoreResult = apps.get_model('competitions', 'TechnicalScoreResult')
    
    JudgeSubmissionStatus = apps.get_model('competitions', 'JudgeSubmissionStatus')
    JudgeSubmissionStatusResult = apps.get_model('competitions', 'JudgeSubmissionStatusResult')
    
    try:
        # Migrate TechnicalPerformance data
        for original in TechnicalPerformance.objects.all():
            TechnicalPerformanceResult.objects.create(
                id=original.id,
                practitioner_id=original.practitioner_id,
                category_id=original.category_id,
                competition_id=original.competition_id,
                performance_order=original.performance_order,
                start_time=original.start_time,
                end_time=original.end_time,
                status=original.status if original.status in ['pending', 'in_progress', 'completed', 'disqualified'] else 'pending',
                notes=original.notes,
                created_at=original.created_at if hasattr(original, 'created_at') else None
            )
    except Exception as e:
        print(f"Error migrating TechnicalPerformance data: {e}")
    
    try:
        # Migrate TechnicalScore data
        for original in TechnicalScore.objects.all():
            # Find corresponding TechnicalPerformanceResult
            try:
                performance_result = TechnicalPerformanceResult.objects.get(
                    practitioner_id=original.performance.practitioner_id,
                    category_id=original.performance.category_id,
                    competition_id=original.performance.competition_id
                )
                
                TechnicalScoreResult.objects.create(
                    performance=performance_result,
                    judge_id=original.judge_id,
                    criterion_id=original.criterion_id,
                    value=original.value,
                    is_locked=original.is_locked if hasattr(original, 'is_locked') else False,
                    is_training_score=original.is_training_score if hasattr(original, 'is_training_score') else False,
                    comments='',  # Default empty comments
                    submitted_at=original.submitted_at if hasattr(original, 'submitted_at') else None
                )
            except TechnicalPerformanceResult.DoesNotExist:
                print(f"Could not find matching TechnicalPerformanceResult for TechnicalScore {original.id}")
                continue
            except Exception as inner_e:
                print(f"Error processing TechnicalScore {original.id}: {inner_e}")
                continue
    except Exception as e:
        print(f"Error migrating TechnicalScore data: {e}")
    
    try:
        # Migrate JudgeSubmissionStatus data
        for original in JudgeSubmissionStatus.objects.all():
            try:
                performance_result = TechnicalPerformanceResult.objects.get(
                    practitioner_id=original.performance.practitioner_id,
                    category_id=original.performance.category_id,
                    competition_id=original.performance.competition_id
                )
                
                JudgeSubmissionStatusResult.objects.create(
                    judge_id=original.judge_id,
                    performance=performance_result,
                    is_submitted=original.submitted if hasattr(original, 'submitted') else False,
                    submitted_at=original.submission_time if hasattr(original, 'submission_time') else None
                )
            except TechnicalPerformanceResult.DoesNotExist:
                print(f"Could not find matching TechnicalPerformanceResult for JudgeSubmissionStatus {original.id}")
                continue
            except Exception as inner_e:
                print(f"Error processing JudgeSubmissionStatus {original.id}: {inner_e}")
                continue
    except Exception as e:
        print(f"Error migrating JudgeSubmissionStatus data: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0004_update_related_names'),
    ]

    operations = [
        migrations.RunPython(forward_data_migration, migrations.RunPython.noop),
    ]