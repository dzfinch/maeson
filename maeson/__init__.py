"""Top-level package for maeson."""

__author__ = """Dryver Finch"""
__email__ = "dryver2206@gmail.com"
__version__ = "0.0.1"

# Import the function from its module
from .gps_metrics import calculate_accuracy_metrics

# Optionally, define __all__ to control what gets imported with `from maeson import *`
__all__ = ["calculate_accuracy_metrics"]
