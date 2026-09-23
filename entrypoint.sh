#!/usr/bin/env bash
# Reproducible local validation entrypoint for FCIL-AndMal.
# Full benchmark execution requires the real CIC-AndMal-2020 files and is
# intentionally never replaced by synthetic data unless --generate-synthetic
# is explicitly supplied for development-only smoke tests.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
WORKSPACE_PACKAGE_DIR="$(cd "${ROOT_DIR}/.." && pwd)/../.pypackages/lib/python${PYTHON_VERSION}/site-packages"
export PYTHONPATH="${WORKSPACE_PACKAGE_DIR}:${ROOT_DIR}:${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1

# macOS Apple Silicon GPU optimization: enable fallback for any ops lacking native MPS kernels
if [[ "$(uname -s)" == "Darwin" ]]; then
  export PYTORCH_ENABLE_MPS_FALLBACK=1
fi

usage() {
  cat <<'EOF'
Usage:
  ./entrypoint.sh test                         Run the complete test suite.
  ./entrypoint.sh smoke                       Run synthetic development smoke tests.
  ./entrypoint.sh prepare --raw-root PATH     Prepare a real dataset only.
  ./entrypoint.sh prepare --root PATH         Prepare a real dataset only.
  ./entrypoint.sh experiment [run_all args]   Run the full benchmark runner.
EOF
}

cd "${ROOT_DIR}"
case "${1:-test}" in
  test)
    python3 -m pytest tests -vv
    ;;
  smoke)
    python3 main.py --mode centralized --feature_type dynamic \
      --method finetune --backbone mlp --rounds_per_task 1 \
      --raw_root "${ROOT_DIR}/.smoke_raw" \
      --prepared_dir "${ROOT_DIR}/.smoke_prepared" \
      --partition_dir "${ROOT_DIR}/.smoke_partitions" \
      --output_root "${ROOT_DIR}/.smoke_experiment" \
      --generate_synthetic --prepare_only
    ;;
  prepare)
    shift
    python3 -m data.prepare_dataset --strict_class_coverage "$@"
    python3 -m data.prepare_dataset "$@"
    ;;
  experiment)
    shift
    python3 run_all.py "$@"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
