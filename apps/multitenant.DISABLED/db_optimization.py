"""
Database optimization utilities for multi-tenant applications.
"""
from typing import Optional, List, Any
from django.db import connection
from django.db.models import QuerySet, Model
from django.conf import settings
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class TenantQueryOptimizer:
    """
    Query optimization strategies for multi-tenant databases.
    """
    
    @staticmethod
    def add_tenant_filter(queryset: QuerySet, tenant_field: str = 'tenant') -> QuerySet:
        """
        Add tenant filter to queryset for proper indexing.
        """
        if hasattr(connection, 'tenant'):
            return queryset.filter(**{tenant_field: connection.tenant})
        return queryset
    
    @staticmethod
    def prefetch_for_tenant(queryset: QuerySet, prefetch_list: List[str]) -> QuerySet:
        """
        Optimized prefetch for tenant-scoped queries.
        """
        return queryset.prefetch_related(*prefetch_list)
    
    @staticmethod
    def select_for_tenant(queryset: QuerySet, select_list: List[str]) -> QuerySet:
        """
        Optimized select_related for tenant-scoped queries.
        """
        return queryset.select_related(*select_list)
    
    @staticmethod
    @contextmanager
    def tenant_connection_pool(schema_name: str):
        """
        Use connection pooling for tenant-specific operations.
        """
        original_schema = connection.schema_name
        try:
            connection.set_schema(schema_name)
            yield connection
        finally:
            connection.set_schema(original_schema)
    
    @staticmethod
    def batch_create(model_class: type[Model], objects: List[Model], batch_size: int = 100):
        """
        Batch create objects with tenant context.
        """
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model_class.objects.bulk_create(batch)
    
    @staticmethod
    def batch_update(model_class: type[Model], objects: List[Model], fields: List[str], batch_size: int = 100):
        """
        Batch update objects with tenant context.
        """
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model_class.objects.bulk_update(batch, fields)


class IndexManager:
    """
    Manage indexes for tenant tables.
    """
    
    @staticmethod
    def create_tenant_indexes(tenant_schema: str):
        """
        Create optimized indexes for tenant schema.
        """
        indexes = [
            # Common lookups
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_competition_date ON competitions_competition(date);",
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_registration_status ON competitions_registration(status);",
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_practitioner_club ON competitions_practitioner(club_id);",
            
            # Performance critical
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_category_name ON competitions_category(name);",
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_match_competition ON competitions_match(competition_id);",
            
            # Composite indexes
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_competition_status_date ON competitions_competition(status, date);",
            f"CREATE INDEX IF NOT EXISTS idx_{tenant_schema}_registration_competition_status ON competitions_registration(competition_id, status);",
        ]
        
        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    cursor.execute(index)
                    logger.info(f"Created index for schema {tenant_schema}")
                except Exception as e:
                    logger.error(f"Failed to create index: {e}")
    
    @staticmethod
    def analyze_tenant_tables(tenant_schema: str):
        """
        Analyze tables for query optimization.
        """
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname = %s;
            """, [tenant_schema])
            
            tables = cursor.fetchall()
            for schema, table in tables:
                cursor.execute(f"ANALYZE {schema}.{table};")
                logger.info(f"Analyzed table {schema}.{table}")


class QueryCache:
    """
    Query result caching for expensive operations.
    """
    
    def __init__(self, cache_backend='default'):
        from .cache import TenantCache
        self.cache = TenantCache(cache_backend)
    
    def cached_count(self, queryset: QuerySet, cache_key: str, timeout: int = 300) -> int:
        """
        Cache count() operations.
        """
        count = self.cache.get(cache_key)
        if count is None:
            count = queryset.count()
            self.cache.set(cache_key, count, timeout)
        return count
    
    def cached_aggregate(self, queryset: QuerySet, aggregation: dict, cache_key: str, timeout: int = 300) -> dict:
        """
        Cache aggregate operations.
        """
        result = self.cache.get(cache_key)
        if result is None:
            result = queryset.aggregate(**aggregation)
            self.cache.set(cache_key, result, timeout)
        return result
    
    def cached_list(self, queryset: QuerySet, cache_key: str, timeout: int = 300) -> List[Any]:
        """
        Cache list operations.
        """
        results = self.cache.get(cache_key)
        if results is None:
            results = list(queryset)
            self.cache.set(cache_key, results, timeout)
        return results


class PerformanceMonitor:
    """
    Monitor query performance for tenants.
    """
    
    @staticmethod
    def log_slow_queries(threshold_ms: int = 100):
        """
        Log queries that exceed threshold.
        """
        from django.db import connections
        
        for alias in connections:
            connection = connections[alias]
            for query in connection.queries:
                time_ms = float(query['time']) * 1000
                if time_ms > threshold_ms:
                    logger.warning(
                        f"Slow query detected ({time_ms:.2f}ms): {query['sql'][:200]}..."
                    )
    
    @staticmethod
    def get_query_stats(tenant_schema: str) -> dict:
        """
        Get query statistics for a tenant.
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    max_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE query LIKE %s
                ORDER BY mean_exec_time DESC
                LIMIT 20;
            """, [f"%{tenant_schema}%"])
            
            return {
                'slow_queries': cursor.fetchall(),
                'tenant_schema': tenant_schema
            }


# Decorators for common optimizations
def cached_tenant_method(cache_key_template: str, timeout: int = 300):
    """
    Decorator to cache tenant-specific method results.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            from .cache import TenantCache
            cache = TenantCache()
            
            # Generate cache key
            cache_key = cache_key_template.format(
                tenant_id=getattr(self, 'tenant_id', 'unknown'),
                **kwargs
            )
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is None:
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def optimized_tenant_query(select_related: List[str] = None, prefetch_related: List[str] = None):
    """
    Decorator to optimize tenant queries.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            queryset = func(self, *args, **kwargs)
            
            if select_related:
                queryset = queryset.select_related(*select_related)
            
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)
            
            return queryset
        return wrapper
    return decorator