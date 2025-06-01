"""
Utilitaires pour gérer les schémas PostgreSQL
"""
from django.db import connection
import logging

logger = logging.getLogger(__name__)


def set_schema(schema_name):
    """
    Configure le schéma PostgreSQL pour la connexion courante.
    Ignore la commande pour SQLite qui ne supporte pas les schémas.
    """
    if not schema_name:
        schema_name = 'public'
    
    # Vérifier le type de base de données
    if connection.vendor == 'sqlite':
        # SQLite ne supporte pas les schémas - ignorer silencieusement
        logger.debug(f"SQLite détecté - ignorer set_schema pour: {schema_name}")
        connection.schema_name = schema_name
        return
    
    with connection.cursor() as cursor:
        # Échapper le nom du schéma pour éviter les injections SQL
        schema_name = connection.ops.quote_name(schema_name)
        cursor.execute(f'SET search_path TO {schema_name}')
        logger.debug(f"Schéma défini sur: {schema_name}")
        
    # Stocker le schéma dans la connexion pour référence future
    connection.schema_name = schema_name


def get_current_schema():
    """
    Obtient le schéma actuellement configuré.
    """
    return getattr(connection, 'schema_name', 'public')


def create_schema(schema_name):
    """
    Crée un nouveau schéma PostgreSQL.
    Ignore la commande pour SQLite qui ne supporte pas les schémas.
    """
    if connection.vendor == 'sqlite':
        logger.debug(f"SQLite détecté - ignorer create_schema pour: {schema_name}")
        return
        
    with connection.cursor() as cursor:
        schema_name = connection.ops.quote_name(schema_name)
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
        logger.info(f"Schéma créé: {schema_name}")


def drop_schema(schema_name):
    """
    Supprime un schéma PostgreSQL.
    Ignore la commande pour SQLite qui ne supporte pas les schémas.
    """
    if connection.vendor == 'sqlite':
        logger.debug(f"SQLite détecté - ignorer drop_schema pour: {schema_name}")
        return
        
    with connection.cursor() as cursor:
        schema_name = connection.ops.quote_name(schema_name)
        cursor.execute(f'DROP SCHEMA IF EXISTS {schema_name} CASCADE')
        logger.warning(f"Schéma supprimé: {schema_name}")


def schema_exists(schema_name):
    """
    Vérifie si un schéma existe.
    Pour SQLite, retourne toujours True car il n'y a pas de schémas séparés.
    """
    if connection.vendor == 'sqlite':
        # SQLite n'a pas de schémas - tous les objets sont dans le schéma principal
        return True
        
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = %s
            )
        """, [schema_name])
        return cursor.fetchone()[0]


def list_schemas():
    """
    Liste tous les schémas disponibles.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """)
        return [row[0] for row in cursor.fetchall()]


class SchemaContext:
    """
    Gestionnaire de contexte pour exécuter du code dans un schéma spécifique.
    """
    def __init__(self, schema_name):
        self.schema_name = schema_name
        self.previous_schema = None
    
    def __enter__(self):
        self.previous_schema = get_current_schema()
        set_schema(self.schema_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_schema(self.previous_schema)