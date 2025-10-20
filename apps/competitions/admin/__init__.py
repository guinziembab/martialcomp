# Import all admin modules EXCEPT practitioner
try:
  from . import user
  from . import competition
  from . import discipline
  from . import category
  from . import club
  from . import judge
  from . import registration
  from . import federation
  from . import qr_code
  # NE PAS importer practitioner
except ImportError as e:
  import logging
  logger = logging.getLogger(__name__)
  logger.error(f"Error importing admin modules: {e}")
