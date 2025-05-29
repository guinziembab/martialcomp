from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL
            """
            -- Create StandaloneScoringSystem table
            CREATE TABLE IF NOT EXISTS competitions_standalonescoringystem (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                system_type VARCHAR(20) NOT NULL,
                min_score DECIMAL(5,2) NOT NULL,
                max_score DECIMAL(5,2) NOT NULL,
                score_step DECIMAL(5,2) NOT NULL,
                exclude_extreme_scores BOOLEAN NOT NULL,
                allow_ties BOOLEAN NOT NULL,
                real_time_results BOOLEAN NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );

            -- Rename the column order to order_num to avoid SQL keyword issues
            -- Create StandaloneScoringCriterion table
            CREATE TABLE IF NOT EXISTS competitions_standalonescoringcriterion (
                id SERIAL PRIMARY KEY,
                scoring_system_id INTEGER NOT NULL REFERENCES competitions_standalonescoringystem(id) ON DELETE CASCADE,
                category_id INTEGER NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                weight DECIMAL(5,2) NOT NULL,
                min_score DECIMAL(5,2) NULL,
                max_score DECIMAL(5,2) NULL,
                step DECIMAL(5,2) NULL,
                order_num INTEGER NOT NULL,
                is_active BOOLEAN NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );

            -- Create StandaloneCategoryScoringConfig table
            CREATE TABLE IF NOT EXISTS competitions_standalonecategoryscoringconfig (
                id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL UNIQUE,
                scoring_system_id INTEGER NOT NULL REFERENCES competitions_standalonescoringystem(id) ON DELETE CASCADE,
                override_min_score DECIMAL(5,2) NULL,
                override_max_score DECIMAL(5,2) NULL,
                override_score_step DECIMAL(5,2) NULL,
                exclude_extreme_scores BOOLEAN NULL,
                allow_ties BOOLEAN NULL,
                real_time_results BOOLEAN NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );

            -- Create StandalonePerformance table
            CREATE TABLE IF NOT EXISTS competitions_standaloneperformance (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                practitioner_id INTEGER NOT NULL,
                round_type VARCHAR(20) NOT NULL,
                round_number INTEGER NOT NULL,
                performance_order INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL,
                start_time TIMESTAMP WITH TIME ZONE NULL,
                end_time TIMESTAMP WITH TIME ZONE NULL,
                duration INTERVAL NULL,
                notes TEXT NOT NULL,
                disqualification_reason TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );

            -- Create StandaloneScore table
            CREATE TABLE IF NOT EXISTS competitions_standalonescore (
                id SERIAL PRIMARY KEY,
                performance_id INTEGER NOT NULL REFERENCES competitions_standaloneperformance(id) ON DELETE CASCADE,
                judge_id INTEGER NOT NULL,
                criterion_id INTEGER NOT NULL REFERENCES competitions_standalonescoringcriterion(id) ON DELETE CASCADE,
                value DECIMAL(5,2) NOT NULL,
                original_value DECIMAL(5,2) NULL,
                is_locked BOOLEAN NOT NULL,
                is_training_score BOOLEAN NOT NULL,
                modified_by_id INTEGER NULL,
                notes TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                UNIQUE(performance_id, judge_id, criterion_id)
            );

            -- Create StandaloneJudgeSubmission table
            CREATE TABLE IF NOT EXISTS competitions_standalonejudgesubmission (
                id SERIAL PRIMARY KEY,
                performance_id INTEGER NOT NULL REFERENCES competitions_standaloneperformance(id) ON DELETE CASCADE,
                judge_id INTEGER NOT NULL,
                is_submitted BOOLEAN NOT NULL,
                submitted_at TIMESTAMP WITH TIME ZONE NULL,
                notes TEXT NOT NULL,
                UNIQUE(performance_id, judge_id)
            );

            -- Create StandaloneJudgeSettings table
            CREATE TABLE IF NOT EXISTS competitions_standalonejudgesettings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                display_mode VARCHAR(20) NOT NULL,
                notification_sounds BOOLEAN NOT NULL,
                auto_submit BOOLEAN NOT NULL,
                theme VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );

            -- Create StandaloneCompetitionRanking table
            CREATE TABLE IF NOT EXISTS competitions_standalonecompetitionranking (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                practitioner_id INTEGER NOT NULL,
                performance_id INTEGER NULL REFERENCES competitions_standaloneperformance(id) ON DELETE SET NULL,
                rank INTEGER NOT NULL,
                final_score DECIMAL(7,3) NOT NULL,
                is_tie BOOLEAN NOT NULL,
                medal VARCHAR(10) NOT NULL,
                is_published BOOLEAN NOT NULL,
                notes TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                UNIQUE(category_id, practitioner_id)
            );

            -- Create StandaloneCategoryRankingSnapshot table
            CREATE TABLE IF NOT EXISTS competitions_standalonecategoryrankingsnapshot (
                id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL,
                competition_id INTEGER NOT NULL,
                created_by_id INTEGER NULL,
                is_published BOOLEAN NOT NULL,
                is_final BOOLEAN NOT NULL,
                name VARCHAR(100) NOT NULL,
                notes TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );

            -- Create StandaloneRankingSnapshotEntry table
            CREATE TABLE IF NOT EXISTS competitions_standalonerankingsnapshotentry (
                id SERIAL PRIMARY KEY,
                snapshot_id INTEGER NOT NULL REFERENCES competitions_standalonecategoryrankingsnapshot(id) ON DELETE CASCADE,
                practitioner_id INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                final_score DECIMAL(7,3) NOT NULL,
                is_tie BOOLEAN NOT NULL,
                medal VARCHAR(10) NOT NULL
            );
            """,
            
            # Reverse SQL
            """
            DROP TABLE IF EXISTS competitions_standalonerankingsnapshotentry;
            DROP TABLE IF EXISTS competitions_standalonecategoryrankingsnapshot;
            DROP TABLE IF EXISTS competitions_standalonecompetitionranking;
            DROP TABLE IF EXISTS competitions_standalonejudgesettings;
            DROP TABLE IF EXISTS competitions_standalonejudgesubmission;
            DROP TABLE IF EXISTS competitions_standalonescore;
            DROP TABLE IF EXISTS competitions_standaloneperformance;
            DROP TABLE IF EXISTS competitions_standalonecategoryscoringconfig;
            DROP TABLE IF EXISTS competitions_standalonescoringcriterion;
            DROP TABLE IF EXISTS competitions_standalonescoringystem;
            """
        )
    ]