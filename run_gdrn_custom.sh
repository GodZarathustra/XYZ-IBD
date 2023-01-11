#!/bin/bash
set -x
PROJECT_DIR=$(dirname $(realpath $0))

blenderproc run $PROJECT_DIR/examples/datasets/gdrn/custom.py
python $PROJECT_DIR/examples/datasets/gdrn/gen_masks.py
python $PROJECT_DIR/examples/datasets/gdrn/gen_annotations.py
