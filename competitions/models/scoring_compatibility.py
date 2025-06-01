from django.db import models
from django.utils.functional import cached_property

"""
This module provides compatibility classes for the transition from the old scoring models
to the new unified scoring system. It allows existing views to continue working with
minimal changes during the transition period.

To use this compatibility layer:
1. Import from this module instead of the original model files
2. Use the models as normal in views
3. Gradually migrate views to use the unified_scoring models directly
"""

# Import the unified models
from .unified_scoring import (
    ScoringSystem, ScoringCriterion, CategoryScoringConfig, 
    Performance, Score, JudgeSubmission, CompetitionRanking,
    CategoryRankingSnapshot, RankingSnapshotEntry, JudgeSettings
)

# Define compatibility classes that inherit from the unified models
# but provide the same interface as the old models

class CompatScoringSystem(ScoringSystem):
    """
    Compatibility class for the old ScoringSystem model.
    """
    class Meta:
        proxy = True

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        # Map specific backward compatibility fields or methods here if needed
        return instance


class CompatScoringCriterion(ScoringCriterion):
    """
    Compatibility class for the old ScoringCriterion model.
    """
    class Meta:
        proxy = True
        
    # Add compatibility methods or properties if needed
    @property
    def get_weight_display(self):
        """Legacy method to display weight with formatting"""
        return f"{self.weight:.1f}x"


class CompatCategoryScoringConfig(CategoryScoringConfig):
    """
    Compatibility class for the old ScoringConfiguration model.
    """
    class Meta:
        proxy = True
    
    # Legacy property names
    @property
    def get_min_score(self):
        return self.get_effective_min_score()
    
    @property
    def get_max_score(self):
        return self.get_effective_max_score()
    
    @property
    def get_score_step(self):
        return self.get_effective_score_step()


class CompatPerformance(Performance):
    """
    Compatibility class for old Performance/TechnicalPerformance models.
    """
    class Meta:
        proxy = True
    
    # Legacy property names
    @property
    def performer(self):
        """Legacy name for practitioner"""
        return self.practitioner
    
    @property
    def order(self):
        """Legacy name for performance_order"""
        return self.performance_order
    
    @property
    def is_completed(self):
        """Legacy property check"""
        return self.status == self.COMPLETED
    
    @property
    def is_disqualified(self):
        """Legacy property check"""
        return self.status == self.DISQUALIFIED
    
    @property
    def judges_count(self):
        """Get count of judges who have submitted scores"""
        return JudgeSubmission.objects.filter(
            performance=self,
            is_submitted=True
        ).count()


class CompatTechnicalPerformance(CompatPerformance):
    """
    Compatibility class specifically for the TechnicalPerformance model.
    """
    class Meta:
        proxy = True


class CompatScore(Score):
    """
    Compatibility class for old Score/TechnicalScore models.
    """
    class Meta:
        proxy = True
    
    @property
    def is_submitted(self):
        """Legacy property check"""
        return self.is_locked
    
    def submit(self):
        """Legacy method to submit a score"""
        return self.lock()


class CompatTechnicalScore(CompatScore):
    """
    Compatibility class specifically for the TechnicalScore model.
    """
    class Meta:
        proxy = True


class CompatJudgeSubmission(JudgeSubmission):
    """
    Compatibility class for old JudgeSubmissionStatus model.
    """
    class Meta:
        proxy = True
    
    @property
    def judge_user(self):
        """Legacy property name"""
        return self.judge
    
    @cached_property
    def all_scores_submitted(self):
        """Check if all scores have been submitted for this performance by this judge"""
        from .unified_scoring import ScoringCriterion
        
        # Get all criteria for this performance's category
        criteria = ScoringCriterion.objects.filter(
            category=self.performance.category
        )
        
        # Get all scores submitted by this judge for this performance
        scores = Score.objects.filter(
            performance=self.performance,
            judge=self.judge,
            is_locked=True
        )
        
        # Check if all criteria have scores
        return scores.count() == criteria.count()


class CompatJudgeSubmissionStatus(CompatJudgeSubmission):
    """
    Compatibility class specifically for the JudgeSubmissionStatus model.
    """
    class Meta:
        proxy = True


class CompatCompetitionRanking(CompetitionRanking):
    """
    Compatibility class for old CompetitionRanking model.
    """
    class Meta:
        proxy = True
    
    @property
    def score(self):
        """Legacy property name"""
        return self.final_score
    
    @property
    def get_medal_display(self):
        """Format medal for display"""
        medals = {
            self.GOLD: "Gold",
            self.SILVER: "Silver",
            self.BRONZE: "Bronze",
            self.NONE: "None"
        }
        return medals.get(self.medal, "None")


# Legacy name mappings for ease of import
# This allows import statements like:
# from competitions.models.scoring_compatibility import TechnicalPerformance
# without changing the class name in the original code

# Scoring Models
ScoringConfiguration = CompatCategoryScoringConfig
TechnicalPerformance = CompatTechnicalPerformance
TechnicalScore = CompatTechnicalScore
JudgeSubmissionStatus = CompatJudgeSubmissionStatus