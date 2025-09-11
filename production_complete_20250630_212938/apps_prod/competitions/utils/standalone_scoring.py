"""
Standalone scoring utilities that don't require model imports.
This prevents import conflicts and provides a self-contained system.
"""

from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional


class StandaloneScoreCalculator:
    """
    Utility class for calculating scores without requiring model imports.
    """
    
    def __init__(self, min_score: float = 0.0, max_score: float = 10.0, 
                 exclude_extreme_scores: bool = False):
        """
        Initialize the calculator with scoring parameters.
        
        Args:
            min_score: Minimum allowed score
            max_score: Maximum allowed score
            exclude_extreme_scores: Whether to exclude extreme scores in calculations
        """
        self.min_score = Decimal(str(min_score))
        self.max_score = Decimal(str(max_score))
        self.exclude_extreme_scores = exclude_extreme_scores
    
    def calculate_weighted_average(self, scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate weighted average score from multiple criteria.
        
        Args:
            scores: List of score dictionaries containing:
                - criterion_id: ID of the criterion
                - criterion_name: Name of the criterion
                - criterion_weight: Weight of the criterion
                - judge_scores: List of scores from judges (numeric values)
        
        Returns:
            Dictionary containing:
                - final_score: Final calculated score
                - criteria_scores: Dictionary of criterion scores
                - judges_count: Number of judges who submitted scores
        """
        if not scores:
            return {
                'final_score': Decimal('0.0'),
                'criteria_scores': {},
                'judges_count': 0
            }
        
        total_weight = Decimal('0.0')
        weighted_sum = Decimal('0.0')
        criteria_scores = {}
        judge_count = 0
        
        # Calculate average for each criterion
        for score_data in scores:
            criterion_id = score_data['criterion_id']
            criterion_name = score_data['criterion_name']
            criterion_weight = Decimal(str(score_data['criterion_weight']))
            judge_scores = score_data['judge_scores']
            
            if not judge_scores:
                criteria_scores[criterion_id] = {
                    'name': criterion_name,
                    'weight': criterion_weight,
                    'average': None,
                    'weighted': None,
                    'judge_count': 0
                }
                continue
            
            # Record the maximum number of judges
            judge_count = max(judge_count, len(judge_scores))
            
            # Convert all scores to Decimal
            decimal_scores = [Decimal(str(s)) for s in judge_scores]
            
            # Handle extreme score exclusion
            if self.exclude_extreme_scores and len(decimal_scores) > 3:
                decimal_scores.remove(max(decimal_scores))
                decimal_scores.remove(min(decimal_scores))
            
            # Calculate average
            avg = sum(decimal_scores) / len(decimal_scores)
            weighted = avg * criterion_weight
            
            # Add to total
            weighted_sum += weighted
            total_weight += criterion_weight
            
            # Store criterion averages
            criteria_scores[criterion_id] = {
                'name': criterion_name,
                'weight': criterion_weight,
                'average': avg,
                'weighted': weighted,
                'judge_count': len(judge_scores)
            }
        
        # Calculate final score
        final_score = Decimal('0.0')
        if total_weight > 0:
            final_score = weighted_sum / total_weight
        
        return {
            'final_score': final_score,
            'criteria_scores': criteria_scores,
            'judges_count': judge_count
        }
    
    def calculate_point_score(self, scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate point-based score (simple sum of all scores).
        
        Args:
            scores: List of score dictionaries (same format as calculate_weighted_average)
        
        Returns:
            Dictionary with final score and details
        """
        if not scores:
            return {
                'final_score': Decimal('0.0'),
                'criteria_scores': {},
                'judges_count': 0
            }
        
        criteria_scores = {}
        judge_count = 0
        total_points = Decimal('0.0')
        
        # Sum all scores for each criterion
        for score_data in scores:
            criterion_id = score_data['criterion_id']
            criterion_name = score_data['criterion_name']
            judge_scores = score_data['judge_scores']
            
            if not judge_scores:
                criteria_scores[criterion_id] = {
                    'name': criterion_name,
                    'sum': Decimal('0.0'),
                    'judge_count': 0
                }
                continue
            
            # Record the maximum number of judges
            judge_count = max(judge_count, len(judge_scores))
            
            # Convert scores to Decimal and sum
            decimal_scores = [Decimal(str(s)) for s in judge_scores]
            criterion_sum = sum(decimal_scores)
            
            # Add to total
            total_points += criterion_sum
            
            # Store criterion sums
            criteria_scores[criterion_id] = {
                'name': criterion_name,
                'sum': criterion_sum,
                'judge_count': len(judge_scores)
            }
        
        return {
            'final_score': total_points,
            'criteria_scores': criteria_scores,
            'judges_count': judge_count
        }
    
    def generate_rankings(self, performance_scores: List[Dict[str, Any]], 
                       allow_ties: bool = True) -> List[Dict[str, Any]]:
        """
        Generate rankings from a list of performance scores.
        
        Args:
            performance_scores: List of dictionaries containing:
                - performance_id: ID of the performance
                - practitioner_id: ID of the practitioner
                - final_score: Final score for the performance
            allow_ties: Whether to allow tied rankings
        
        Returns:
            List of dictionaries containing:
                - performance_id: ID of the performance
                - practitioner_id: ID of the practitioner
                - rank: Final rank
                - final_score: Final score
                - is_tie: Whether this is a tied rank
                - medal: Medal awarded (gold, silver, bronze, or none)
        """
        if not performance_scores:
            return []
        
        # Sort by score (descending)
        performance_scores = sorted(
            performance_scores, 
            key=lambda x: x['final_score'], 
            reverse=True
        )
        
        # Generate rankings
        rankings = []
        current_rank = 1
        previous_score = None
        is_tie = False
        
        for index, item in enumerate(performance_scores):
            performance_id = item['performance_id']
            practitioner_id = item['practitioner_id']
            score = item['final_score']
            
            # Check for ties
            if previous_score is not None and score == previous_score:
                is_tie = True
            else:
                # If ties are not allowed, increment rank even for tied scores
                if not allow_ties or previous_score is None:
                    current_rank = index + 1
                is_tie = False
            
            # Determine medal
            medal = 'none'
            if current_rank == 1:
                medal = 'gold'
            elif current_rank == 2:
                medal = 'silver'
            elif current_rank == 3:
                medal = 'bronze'
            
            # Create ranking entry
            rankings.append({
                'performance_id': performance_id,
                'practitioner_id': practitioner_id,
                'rank': current_rank,
                'final_score': score,
                'is_tie': is_tie,
                'medal': medal
            })
            
            previous_score = score
        
        return rankings
    
    def handle_third_place_tie(self, rankings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Special handling for ties in third place (multiple bronze medals).
        
        Args:
            rankings: List of ranking dictionaries
        
        Returns:
            Updated list of ranking dictionaries
        """
        # Find all ranks with value 3 or 4
        third_place = [r for r in rankings if r['rank'] == 3]
        fourth_place = [r for r in rankings if r['rank'] == 4 and r['is_tie']]
        
        # If we have multiple third places or tied fourth places, award bronze to all
        if len(third_place) > 1 or fourth_place:
            all_bronze = third_place + fourth_place
            
            for rank in all_bronze:
                rank['rank'] = 3
                rank['is_tie'] = len(all_bronze) > 1
                rank['medal'] = 'bronze'
        
        return rankings