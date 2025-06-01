from decimal import Decimal
from django.db.models import Avg, Max, Min, Count
from django.db import transaction
from django.utils import timezone

class ScoreCalculator:
    """
    Centralized utility for calculating scores in various scoring systems.
    """
    
    def __init__(self, performance):
        """
        Initialize with a performance object.
        
        Args:
            performance: A Performance model instance
        """
        self.performance = performance
        self.category = performance.category
        
        # Get scoring configuration for this category
        try:
            self.config = self.category.scoring_config
            self.scoring_system = self.config.scoring_system
        except AttributeError:
            raise ValueError(f"No scoring configuration found for category: {self.category}")
    
    def calculate_final_score(self):
        """
        Calculate the final score based on the scoring system type.
        
        Returns:
            Decimal: The calculated final score
        """
        system_type = self.scoring_system.system_type
        
        if system_type == 'standard':
            return self._calculate_standard_score()
        elif system_type == 'point':
            return self._calculate_point_score()
        elif system_type == 'direct':
            return self._calculate_direct_elimination_score()
        elif system_type == 'custom':
            return self._calculate_custom_score()
        else:
            raise ValueError(f"Unknown scoring system type: {system_type}")
    
    def _calculate_standard_score(self):
        """
        Calculate score using weighted average of criteria scores, 
        optionally excluding extreme scores.
        
        Returns:
            Decimal: The calculated weighted average score
        """
        # Import here to avoid circular imports
        from competitions.models.unified_scoring import Score, ScoringCriterion
        
        # Get all valid scores for this performance
        scores = Score.objects.filter(
            performance=self.performance,
            is_locked=True,
            is_training_score=False
        )
        
        # Check if we have scores to calculate
        if not scores.exists():
            return Decimal('0.0')
        
        # Get all judges who have submitted scores
        judges = set(scores.values_list('judge_id', flat=True))
        
        # Get all criteria for this category
        criteria = ScoringCriterion.objects.filter(
            category=self.category
        )
        
        # Check if we need to exclude extreme scores
        exclude_extremes = self.config.get_effective_exclude_extreme_scores()
        
        total_weighted_score = Decimal('0.0')
        total_weight = Decimal('0.0')
        
        # Calculate score for each criterion separately
        for criterion in criteria:
            criterion_scores = scores.filter(criterion=criterion)
            
            # Skip if no scores for this criterion
            if not criterion_scores.exists():
                continue
            
            values = list(criterion_scores.values_list('value', flat=True))
            
            # Only exclude extreme scores if we have enough judges and it's configured
            if exclude_extremes and len(values) > 3:
                min_value = min(values)
                max_value = max(values)
                
                # Remove one min and one max score
                values.remove(min_value)
                values.remove(max_value)
            
            # Calculate average
            criterion_avg = sum(values) / len(values)
            
            # Apply weight
            total_weighted_score += criterion_avg * criterion.weight
            total_weight += criterion.weight
        
        # Return weighted average
        if total_weight > 0:
            return total_weighted_score / total_weight
        else:
            return Decimal('0.0')
    
    def _calculate_point_score(self):
        """
        Calculate score using a points-based system.
        
        Returns:
            Decimal: The total points earned
        """
        # Import here to avoid circular imports
        from competitions.models.unified_scoring import Score
        
        # Get all valid scores for this performance
        scores = Score.objects.filter(
            performance=self.performance,
            is_locked=True,
            is_training_score=False
        )
        
        # In a point system, simply sum all scores
        total_points = scores.aggregate(sum=models.Sum('value'))['sum'] or Decimal('0.0')
        
        return total_points
    
    def _calculate_direct_elimination_score(self):
        """
        In direct elimination, the score is binary - either win or lose.
        
        Returns:
            Decimal: 1.0 for win, 0.0 for loss
        """
        # Direct elimination scoring is typically handled differently
        # and depends on the specific competition rules
        # This is a placeholder implementation
        return Decimal('0.0')
    
    def _calculate_custom_score(self):
        """
        Calculate score using a custom formula.
        
        Returns:
            Decimal: The calculated custom score
        """
        # Custom scoring systems should be implemented by extending this class
        # and overriding this method
        return self._calculate_standard_score()


class RankingGenerator:
    """
    Utility for generating rankings from performances.
    """
    
    def __init__(self, category):
        """
        Initialize with a category.
        
        Args:
            category: A CompetitionCategory model instance
        """
        self.category = category
        self.competition = category.competition
        
        # Get scoring configuration for this category
        try:
            self.config = self.category.scoring_config
            self.allow_ties = self.config.get_effective_allow_ties()
        except AttributeError:
            # Default to allowing ties if no configuration exists
            self.allow_ties = True
    
    @transaction.atomic
    def generate_rankings(self):
        """
        Generate rankings for all completed performances in this category.
        
        Returns:
            list: A list of CompetitionRanking objects
        """
        # Import here to avoid circular imports
        from competitions.models.unified_scoring import Performance, CompetitionRanking
        
        # Clear existing rankings for this category
        CompetitionRanking.objects.filter(category=self.category).delete()
        
        # Get all completed performances for this category
        performances = Performance.objects.filter(
            category=self.category,
            status=Performance.COMPLETED
        )
        
        # Calculate scores for each performance
        performance_scores = []
        for performance in performances:
            calculator = ScoreCalculator(performance)
            score = calculator.calculate_final_score()
            
            performance_scores.append({
                'performance': performance,
                'score': score,
                'practitioner': performance.practitioner,
            })
        
        # Sort by score (descending)
        performance_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Generate rankings
        rankings = []
        current_rank = 1
        previous_score = None
        is_tie = False
        
        for index, item in enumerate(performance_scores):
            performance = item['performance']
            score = item['score']
            practitioner = item['practitioner']
            
            # Check for ties
            if previous_score is not None and score == previous_score:
                is_tie = True
            else:
                # If ties are not allowed, increment rank even for tied scores
                if not self.allow_ties or previous_score is None:
                    current_rank = index + 1
                is_tie = False
            
            # Create ranking entry
            ranking = CompetitionRanking.objects.create(
                competition=self.competition,
                category=self.category,
                practitioner=practitioner,
                performance=performance,
                rank=current_rank,
                final_score=score,
                is_tie=is_tie
            )
            
            rankings.append(ranking)
            previous_score = score
        
        return rankings
    
    @transaction.atomic
    def handle_third_place_tie(self):
        """
        Special handling for ties in third place.
        In many competitions, ties for third place result in two bronze medals.
        
        Returns:
            bool: True if changes were made, False otherwise
        """
        # Import here to avoid circular imports
        from competitions.models.unified_scoring import CompetitionRanking
        
        # Find all rankings with rank 3
        third_place_rankings = CompetitionRanking.objects.filter(
            category=self.category,
            rank=3
        )
        
        # Also check if there are any with rank 4 marked as ties
        tied_fourth_rankings = CompetitionRanking.objects.filter(
            category=self.category,
            rank=4,
            is_tie=True
        )
        
        # If we have multiple third places or tied fourth places
        if third_place_rankings.count() > 1 or tied_fourth_rankings.exists():
            # Update all to be bronze medalists
            all_bronze = list(third_place_rankings) + list(tied_fourth_rankings)
            
            for ranking in all_bronze:
                ranking.rank = 3
                ranking.is_tie = len(all_bronze) > 1
                ranking.medal = CompetitionRanking.BRONZE
                ranking.save()
            
            return True
        
        return False
    
    @transaction.atomic
    def create_snapshot(self, user=None, name='', notes='', publish=False):
        """
        Create a snapshot of the current rankings.
        
        Args:
            user: The user creating the snapshot
            name: Name for the snapshot
            notes: Additional notes
            publish: Whether to immediately publish the snapshot
            
        Returns:
            CategoryRankingSnapshot: The created snapshot
        """
        # Import here to avoid circular imports
        from competitions.models.unified_scoring import CategoryRankingSnapshot
        
        # Generate rankings if none exist
        if not CompetitionRanking.objects.filter(category=self.category).exists():
            self.generate_rankings()
        
        # Create snapshot
        snapshot = CategoryRankingSnapshot.create_from_current_rankings(
            category=self.category,
            user=user,
            name=name,
            notes=notes
        )
        
        # Publish if requested
        if publish:
            snapshot.publish()
        
        return snapshot