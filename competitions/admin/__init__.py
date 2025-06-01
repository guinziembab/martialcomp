# Import all admin modules to register them with the admin site
try:
    from . import user
    from . import competition
    from . import discipline
    from . import category
    from . import club
    from . import practitioner
    from . import judge
    from . import registration
    from . import federation
    from . import qr_code

except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing admin modules: {e}")
    raise

# This file serves as a central point for all admin registrations