#!/bin/bash
set -x
PROJECT_DIR=$(dirname $(realpath $0))

chown -R 1000:1000 output

if [ -z $1 ]; then
    # use default configuration
    gosu bproc /bin/bash -c "blenderproc run $PROJECT_DIR/examples/datasets/deep-tote/custom.py"
    gosu bproc /bin/bash -c "python $PROJECT_DIR/examples/datasets/deep-tote/gen_masks.py"
    gosu bproc /bin/bash -c "python $PROJECT_DIR/examples/datasets/deep-tote/gen_annotations.py"
else
    # use custom configutation
    gosu bproc /bin/bash -c "blenderproc run $PROJECT_DIR/examples/datasets/deep-tote/custom.py --config $1"
    gosu bproc /bin/bash -c "python $PROJECT_DIR/examples/datasets/deep-tote/gen_masks.py --config $1"
    gosu bproc /bin/bash -c "python $PROJECT_DIR/examples/datasets/deep-tote/gen_annotations.py --config $1"
fi

