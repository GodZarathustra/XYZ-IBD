#!/bin/bash
set -x
PROJECT_DIR=$(dirname $(realpath $0))

if [ -z $1 ]; then
    # use default configuration
    blenderproc run $PROJECT_DIR/examples/datasets/deep-tote/custom.py
    python $PROJECT_DIR/examples/datasets/deep-tote/gen_masks.py
    python $PROJECT_DIR/examples/datasets/deep-tote/gen_annotations.py
else
    # use custom configutation
    blenderproc run $PROJECT_DIR/examples/datasets/deep-tote/custom.py --config $1
    python $PROJECT_DIR/examples/datasets/deep-tote/gen_masks.py --config $1
    python $PROJECT_DIR/examples/datasets/deep-tote/gen_annotations.py --config $1
fi

