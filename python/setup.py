from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

__title__ = "tcpb"
__copyright__ = "Martinez Group, Stanford University, CA, USA, Planet Earth"
__version__ = "0.4.1"
__status__ = "dev"


setup(name="tcpb",
      version=__version__,
      description="Python client for TeraChem Protocol Buffer server",
      packages=["tcpb"],
      test_suite="tcpb",
      long_description="""Python client for TeraChem Protocol Buffer server""",
      # Test with google>=2 and could not import google.protobuf.internal
      install_requires=['google==1.9.3','protobuf>=3.2.0','numpy>=1.13', 'mtzutils>=0.1.0']
      )
