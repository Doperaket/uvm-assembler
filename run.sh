#!/bin/sh
set -e
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python}"

run_program() {
    "$PYTHON" src/assembler.py "programs/$1.csv" "out/$1.bin"
    "$PYTHON" src/interpreter.py "out/$1.bin" "out/$1.csv" "$2"
    cat "out/$1.csv"
}

case "${1:-test}" in
    test)
        "$PYTHON" -m unittest
        ;;
    demo)
        mkdir -p out
        run_program copy_array 400-404
        run_program sqrt_demo 300-300
        run_program sqrt_vector 300-304
        run_program example_squares 300-304
        run_program example_rounding 300-304
        run_program example_chain 200-204
        ;;
    *)
        echo "Использование: ./run.sh [test|demo]" >&2
        exit 2
        ;;
esac
