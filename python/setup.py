from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

__title__ = "tcpb"
__copyright__ = "Martinez Group, Stanford University, CA, USA, Planet Earth"
__version__ = "0.1.0"
__status__ = "alpha"


setup(name="tcpb",
      version=__version__,
      description="Python client for TeraChem Protocol Buffer server",
      packages=["tcpb"],
      test_suite="tcpb",
      long_description="""This is still very much a work in progress.""",
      install_requires=['protobuf>=3.2.0','numpy>=1.13']
      )
