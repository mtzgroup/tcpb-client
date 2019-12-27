#!/bin/bash
# Build several versions and architectures of conda package
# Modified from https://medium.com/@giswqs/building-a-conda-package-and-uploading-it-to-anaconda-cloud-6a3abd1c5c52

# Settings
PKG=tcpb
CONDA_BLD_DIR=$HOME/opt/anaconda3/conda-bld/
versions=( 2.7 3.5 3.6 3.7 3.8 )
archs=( osx-64 linux-32 linux-64 win-32 win-64)

# Purge builds (not sure how useful)
conda build purge

# Python versions
for py in "${versions[@]}"; do
  echo ">>> Building for Python $py <<<"
  conda-build --python $py --no-anaconda-upload .
done

# Architectures (assuming currently on Mac)
find $CONDA_BLD_DIR/osx-64 -name $PKG-*.tar.bz2 | while read file; do
  for arch in "${archs[@]}"; do
    echo ">>> Converting $file to platform $arch <<<"
    conda convert --platform $arch $file -o $CONDA_BLD_DIR
  done 
done

# Upload (skipping in case rerunning with new versions/archs)
find $CONDA_BLD_DIR -name $PKG-*.tar.bz2 | while read file; do
  echo ">>> Uploading $file to Anaconda Cloud <<<"
  anaconda upload -u mtzgroup $file --skip
done
