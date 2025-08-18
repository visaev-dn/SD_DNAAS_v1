# Tests Package
# Comprehensive testing framework for the modular API

__version__ = "1.0.0"
__description__ = "Testing framework for lab automation modular API"

from .unit import *
from .integration import *
from .performance import *

__all__ = ['unit', 'integration', 'performance']
