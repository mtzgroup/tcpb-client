"""Protobuf client for TeraChem server mode"""

from importlib import metadata

from .clients import TCFrontEndClient, TCProtobufClient  # noqa

__version__ = metadata.version(__name__)
