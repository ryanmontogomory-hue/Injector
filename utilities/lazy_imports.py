"""
Lazy import system for heavy modules to improve startup performance.
"""

import sys
import importlib
from typing import Any, Dict, Optional
from functools import wraps

# Cache for lazy-loaded modules
_lazy_module_cache: Dict[str, Any] = {}


class LazyModuleLoader:
    """Lazy loader for modules that should only be imported when needed."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name: str) -> Any:
        """Lazy load the module when an attribute is accessed."""
        if self._module is None:
            self._module = self._import_module()
        return getattr(self._module, name)
    
    def _import_module(self) -> Any:
        """Import the module and cache it."""
        if self.module_name in _lazy_module_cache:
            return _lazy_module_cache[self.module_name]
        
        try:
            module = importlib.import_module(self.module_name)
            _lazy_module_cache[self.module_name] = module
            return module
        except ImportError as e:
            # Return a mock module that raises an error when used
            return MockModule(self.module_name, str(e))


class MockModule:
    """Mock module for when lazy imports fail."""
    
    def __init__(self, module_name: str, error_message: str):
        self.module_name = module_name
        self.error_message = error_message
    
    def __getattr__(self, name: str) -> Any:
        raise ImportError(f"Failed to lazy load {self.module_name}: {self.error_message}")


def lazy_import(module_name: str) -> LazyModuleLoader:
    """Create a lazy loader for a module."""
    return LazyModuleLoader(module_name)


def lazy_function_import(module_name: str, function_name: str):
    """Decorator to lazy import a function from a module."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Import the module and function when needed
            if module_name not in _lazy_module_cache:
                try:
                    _lazy_module_cache[module_name] = importlib.import_module(module_name)
                except ImportError as e:
                    raise ImportError(f"Failed to lazy load {module_name} for {function_name}: {e}")
            
            module = _lazy_module_cache[module_name]
            actual_function = getattr(module, function_name)
            return actual_function(*args, **kwargs)
        
        return wrapper
    return decorator


class LazyComponentManager:
    """Manages lazy loading of UI components."""
    
    def __init__(self):
        self.loaded_components: Dict[str, bool] = {}
    
    def should_load_component(self, component_name: str, condition: bool = True) -> bool:
        """Check if a component should be loaded based on conditions."""
        if not condition:
            return False
        
        if component_name not in self.loaded_components:
            self.loaded_components[component_name] = True
            return True
        
        return True
    
    def mark_component_loaded(self, component_name: str) -> None:
        """Mark a component as loaded."""
        self.loaded_components[component_name] = True
    
    def is_component_loaded(self, component_name: str) -> bool:
        """Check if a component has been loaded."""
        return self.loaded_components.get(component_name, False)


# Global instance for managing lazy components
lazy_component_manager = LazyComponentManager()


def lazy_streamlit_component(component_name: str, condition: bool = True):
    """Decorator for lazy loading Streamlit components."""
    def decorator(render_func):
        @wraps(render_func)
        def wrapper(*args, **kwargs):
            if lazy_component_manager.should_load_component(component_name, condition):
                return render_func(*args, **kwargs)
            return None
        return wrapper
    return decorator


# Pre-defined lazy imports for heavy modules
lazy_pandas = lazy_import('pandas')
lazy_numpy = lazy_import('numpy')
lazy_docx = lazy_import('docx')
lazy_psutil = lazy_import('psutil')

# Google Drive picker - heavy to load
lazy_gdrive = lazy_import('ui.gdrive_picker')

# Email handling - has external dependencies
lazy_email = lazy_import('email_handler')

# Document processing - can be heavy for large documents
lazy_doc_processor = lazy_import('document_processor')


def get_lazy_module_stats() -> Dict[str, Any]:
    """Get statistics about lazy-loaded modules."""
    return {
        'loaded_modules': list(_lazy_module_cache.keys()),
        'loaded_count': len(_lazy_module_cache),
        'component_stats': lazy_component_manager.loaded_components
    }


def clear_lazy_cache() -> None:
    """Clear the lazy import cache."""
    global _lazy_module_cache
    _lazy_module_cache.clear()
    lazy_component_manager.loaded_components.clear()


def preload_essential_modules() -> None:
    """Preload essential modules that will definitely be needed."""
    try:
        # Preload core modules that are always used
        import logger
        import config
        import performance_monitor
        
        _lazy_module_cache.update({
            'logger': logger,
            'config': config,
            'performance_monitor': performance_monitor
        })
    except Exception as e:
        # Don't fail if preloading fails
        pass



