#!/bin/bash
conda config --append channels conda-forge
conda create -q -n test-environment python=$TRAVIS_PYTHON_VERSION
source activate test-environment
conda install --file ci/"$JOB_NAME".txt
