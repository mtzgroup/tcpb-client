#!/bin/sh -e

set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place tcpb tests examples --exclude=__init__.py
black tcpb tests examples
isort tcpb tests examples
