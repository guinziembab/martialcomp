# -*- coding: utf-8 -*-
"""
Middleware pour l'optimisation des performances des événements.
Analyse les requÃªtes, identifie les problèmes de performances et fournit des conseils d'optimisation.
"""

import time
import logging
import json
import re
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuration
PERFORMANCE_THRESHOLD_MS = getattr(settings, 'PERFORMANCE_THRESHOLD_MS', 500)  # Seuil en millisecondes
QUERY_THRESHOLD_MS = getattr(settings, 'QUERY_THRESHOLD_MS', 100)  # Seuil pour les requÃªtes SQL lentes
MAX_QUERIES_WARNING = getattr(settings, 'MAX_QUERIES_WARNING', 30)  # Nombre max de requÃªtes avant avertissement

# URLs liées aux événements Ã  surveiller
EVENT_URL_PATTERNS = [
    r'^/competitions/events/',
    r'^/competitions/event_planning/',
    r'^/competitions/events/surveys/',
]


class EventPerformanceMiddleware(MiddlewareMixin):
    """
    Middleware qui surveille et analyse les performances des pages liées aux événements.
    Fournit des informations de diagnostic pour optimiser le temps de réponse.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def process_request(self, request):
        """Initialise le suivi des performances pour cette requÃªte."""
        if not settings.DEBUG:
            return None
        
        # Vérifier si l'URL correspond Ã  un motif d'événement
        if not any(re.match(pattern, request.path) for pattern in EVENT_URL_PATTERNS):
            return None
        
        # Marquer le début du temps d'exécution
        request.performance_start_time = time.time()
        request.performance_start_queries = len(connection.queries)
        
        return None
    
    def process_response(self, request, response):
        """Analyse les performances après le traitement de la requÃªte."""
        if not settings.DEBUG or not hasattr(request, 'performance_start_time'):
            return response
        
        # Calculer les métriques de performance
        execution_time = time.time() - request.performance_start_time
        execution_time_ms = execution_time * 1000
        
        # Compter les requÃªtes
        end_queries = len(connection.queries)
        num_queries = end_queries - request.performance_start_queries
        
        # Analyser les performances
        if execution_time_ms > PERFORMANCE_THRESHOLD_MS or num_queries > MAX_QUERIES_WARNING:
            # Analyse des requÃªtes SQL
            slow_queries = []
            similar_queries = {}
            query_times = []
            
            if num_queries > 0:
                # Analyser uniquement les requÃªtes de cette requÃªte
                relevant_queries = connection.queries[request.performance_start_queries:end_queries]
                
                # Identifier les requÃªtes lentes
                for query in relevant_queries:
                    query_time_ms = float(query.get('time', 0)) * 1000
                    query_times.append(query_time_ms)
                    
                    # Capturer les requÃªtes lentes
                    if query_time_ms > QUERY_THRESHOLD_MS:
                        sql = query.get('sql', '')
                        slow_queries.append({
                            'time_ms': query_time_ms,
                            'sql': sql[:300] + ('...' if len(sql) > 300 else '')
                        })
                    
                    # Détecter les requÃªtes similaires (potentiel N+1)
                    # Simplifier la requÃªte pour la comparaison
                    sql = query.get('sql', '')
                    # Supprimer les valeurs spécifiques pour comparer la structure
                    simplified_sql = re.sub(r'\'[^\']*\'', "'?'", sql)
                    simplified_sql = re.sub(r'\d+', "N", simplified_sql)
                    
                    if simplified_sql in similar_queries:
                        similar_queries[simplified_sql]['count'] += 1
                        similar_queries[simplified_sql]['time_ms'] += query_time_ms
                    else:
                        similar_queries[simplified_sql] = {
                            'count': 1,
                            'time_ms': query_time_ms,
                            'example': sql[:100] + ('...' if len(sql) > 100 else '')
                        }
            
            # Détecter les patterns N+1
            n_plus_one_candidates = {
                sql: data for sql, data in similar_queries.items()
                if data['count'] > 5 and 'SELECT' in sql.upper()
            }
            
            # Préparer le rapport de performance
            performance_report = {
                'url': request.path,
                'execution_time_ms': execution_time_ms,
                'query_count': num_queries,
                'total_query_time_ms': sum(query_times),
                'max_query_time_ms': max(query_times) if query_times else 0,
                'avg_query_time_ms': sum(query_times) / len(query_times) if query_times else 0,
                'slow_queries': slow_queries,
                'n_plus_one_candidates': [
                    {
                        'pattern': pattern,
                        'count': data['count'],
                        'total_time_ms': data['time_ms'],
                        'example': data['example']
                    }
                    for pattern, data in n_plus_one_candidates.items()
                ],
                'optimization_suggestions': []
            }
            
            # Générer des suggestions d'optimisation
            if num_queries > MAX_QUERIES_WARNING:
                performance_report['optimization_suggestions'].append(
                    f"Nombre élevé de requÃªtes ({num_queries}). "
                    f"Considérez utiliser select_related/prefetch_related pour réduire le nombre de requÃªtes."
                )
            
            if n_plus_one_candidates:
                performance_report['optimization_suggestions'].append(
                    f"Potentiel problème N+1 détecté: {len(n_plus_one_candidates)} modèles de requÃªtes répétés. "
                    f"Utilisez prefetch_related ou select_related."
                )
            
            if slow_queries:
                performance_report['optimization_suggestions'].append(
                    f"{len(slow_queries)} requÃªtes lentes détectées (>100ms). "
                    f"Considérez optimiser ces requÃªtes avec des index ou refactoriser."
                )
            
            if execution_time_ms > PERFORMANCE_THRESHOLD_MS:
                performance_report['optimization_suggestions'].append(
                    f"Temps de réponse élevé ({execution_time_ms:.2f}ms). "
                    f"Envisagez d'ajouter de la mise en cache pour cette vue."
                )
            
            # Loguer le rapport de performance
            logger.warning(f"Performance issue detected: {json.dumps(performance_report, indent=2)}")
            
            # En mode debug, ajouter les informations de performance Ã  la réponse
            if settings.DEBUG and 'text/html' in response.get('Content-Type', ''):
                performance_html = f"""
                <div id="performance-report" style="position: fixed; bottom: 0; right: 0; background: #fff8e1; border: 1px solid #ffecb3; padding: 10px; z-index: 10000; max-width: 600px; max-height: 300px; overflow: auto; font-family: monospace; font-size: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #ff6f00;">Performance Warning</h3>
                    <p><strong>Execution Time:</strong> {execution_time_ms:.2f}ms</p>
                    <p><strong>Queries:</strong> {num_queries}</p>
                    <p><strong>Suggestions:</strong></p>
                    <ul style="padding-left: 20px;">
                        {''.join(f'<li>{suggestion}</li>' for suggestion in performance_report['optimization_suggestions'])}
                    </ul>
                    <button onclick="document.getElementById('performance-report').style.display='none';" style="position: absolute; top: 5px; right: 5px; background: none; border: none; cursor: pointer;">âœ•</button>
                </div>
                """
                
                # Insérer le rapport avant la balise de fermeture </body>
                response_content = response.content.decode('utf-8')
                response_content = response_content.replace('</body>', performance_html + '</body>')
                response.content = response_content.encode('utf-8')
        
        return response


class EventCacheMiddleware(MiddlewareMixin):
    """
    Middleware pour la gestion du cache des pages d'événements.
    Optimise la mise en cache des pages fréquemment consultées.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def process_request(self, request):
        """
        Vérifie si la page demandée est en cache et la retourne si c'est le cas.
        Ne met en cache que les pages publiques (GET sans authentification).
        """
        # Ne pas mettre en cache les requÃªtes POST, les pages admin, ou les utilisateurs connectés
        if (request.method != 'GET' or
            request.path.startswith('/admin/') or
            request.user.is_authenticated):
            return None
        
        # Vérifier si l'URL correspond Ã  un motif d'événement public
        if not any(re.match(pattern, request.path) for pattern in EVENT_URL_PATTERNS):
            return None
        
        # TODO: Implémenter la logique de cache ici si nécessaire
        
        return None
    
    def process_response(self, request, response):
        """
        Met en cache les réponses pour les pages d'événements publiques.
        """
        # Ne pas mettre en cache les erreurs, les pages non-GET, ou les utilisateurs connectés
        if (request.method != 'GET' or
            response.status_code != 200 or
            request.path.startswith('/admin/') or
            request.user.is_authenticated):
            return response
        
        # Vérifier si l'URL correspond Ã  un motif d'événement public
        if not any(re.match(pattern, request.path) for pattern in EVENT_URL_PATTERNS):
            return response
        
        # TODO: Implémenter la logique de mise en cache ici si nécessaire
        
        return response
