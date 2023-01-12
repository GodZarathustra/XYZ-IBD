#!/bin/bash
set -x
PROJECT_DIR=$(dirname $(realpath $0))

blenderproc run $PROJECT_DIR/examples/datasets/deep-tote/custom.py
python $PROJECT_DIR/examples/datasets/deep-tote/gen_masks.py
python $PROJECT_DIR/examples/datasets/deep-tote/gen_annotations.py
