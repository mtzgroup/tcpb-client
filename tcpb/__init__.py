"""Protobuf client for TeraChem server mode"""

from importlib import metadata as _metadata

from .clients import TCFrontEndClient, TCProtobufClient  # noqa

try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:
    # Source tree / build hook / CI checkout
    __version__ = "0.0.0+local"
