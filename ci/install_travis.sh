#!/bin/bash
conda config --append channels conda-forge
conda create -q -n test-environment python=$TRAVIS_PYTHON_VERSION numpy contextlib2 mock openjpeg
source activate test-environment
