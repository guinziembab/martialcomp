# Expose urlpatterns for include('apps.finances.api') by delegating to the api.py file
# Import directly from the parent module's api.py file
import importlib
import sys

# Import the api.py file (not this package)
_api_module_path = 'apps.finances.api'
# Remove this package from cache if it exists to avoid recursion
if _api_module_path in sys.modules:
    _api_file = sys.modules.get(_api_module_path)
    # Check if this is the package (directory) not the file
    if hasattr(_api_file, '__path__'):
        # This is the package, need to load the file
        del sys.modules[_api_module_path]

# Import from the actual api.py file using importlib.util
import importlib.util
import os

_api_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api.py')
_spec = importlib.util.spec_from_file_location("apps.finances.api_file", _api_file_path)
_api_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_api_module)

# Expose urlpatterns from the loaded module
urlpatterns = _api_module.urlpatterns