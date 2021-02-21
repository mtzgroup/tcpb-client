from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

__title__ = "TeraChem Protocol Buffer Client"
__copyright__ = "Martinez Group, Stanford University, CA, USA, Planet Earth"
__version__ = "0.1.0"
__status__ = "beta"


setup(name="tcpb",
      version=__version__,
      description="Python client for TeraChem Protocol Buffer server",
      long_description=readme(),
      packages=['tcpb'],
      test_suite="tcpb",
      install_requires=['google==1.9.3','protobuf>=3.2.0','numpy>=1.13','future'],
      python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
      url='https://github.com/mtzgroup/tcpb-client',
      project_urls={
          'Source': 'https://github.com/mtzgroup/tcpb-client',
          'Tracker': 'https://github.com/mtzgroup/tcpb-client/issues',
          'Documentation': 'https://mtzgrouptcpb.readthedocs.io/en/latest/index.html'
      },
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Utilities',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
      ],
      )
