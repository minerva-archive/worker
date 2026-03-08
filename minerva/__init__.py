# This declares the __init__ method for the module.0

from importlib.metadata import version

__version__ = version("minerva-worker")

__all__ = ["__version__"]
