#!/usr/bin/env bash
# ==============================================================================
# Setup & Verification Script for macOS (Apple Silicon GPU / Metal MPS)
# Project: FCIL-AndMal (Federated Continual Learning for Android Malware)
# ==============================================================================

set -euo pipefail

# ANSI Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

echo -e "\n${BOLD}${CYAN}====================================================================${NC}"
echo -e "${BOLD}${CYAN}      FCIL-AndMal — macOS Apple Silicon (GPU/MPS) Setup Helper      ${NC}"
echo -e "${BOLD}${CYAN}====================================================================${NC}\n"

# 1. Platform & Architecture Validation
OS_NAME="$(uname -s)"
ARCH_NAME="$(uname -m)"

echo -e "  [1/5] Detecting Operating System & Processor Architecture..."
echo -e "        OS           : ${BOLD}${OS_NAME}${NC}"
echo -e "        Architecture : ${BOLD}${ARCH_NAME}${NC}"

if [[ "${OS_NAME}" != "Darwin" ]]; then
    echo -e "  ${YELLOW}⚠ Notice: Current operating system is not Darwin/macOS (${OS_NAME}).${NC}"
    echo -e "            This script is designed for Apple Silicon Macs, but will continue environment checks."
fi

if [[ "${ARCH_NAME}" == "x86_64" ]] && [[ "${OS_NAME}" == "Darwin" ]]; then
    echo -e "  ${YELLOW}⚠ Notice: Running under x86_64 (Rosetta translation).${NC}"
    echo -e "            For 3x-5x faster GPU performance, run using native arm64 Terminal & Python."
elif [[ "${ARCH_NAME}" == "arm64" ]]; then
    echo -e "  ${GREEN}✔ Confirmed: Native Apple Silicon (arm64) architecture detected.${NC}"
fi

# 2. Python Interpreter Check
echo -e "\n  [2/5] Checking Python interpreter..."
if ! command -v python3 &>/dev/null; then
    echo -e "  ${RED}✘ Error: python3 not found on PATH. Please install Python 3.9+ via python.org or Homebrew.${NC}"
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
echo -e "        Python Executable : $(which python3)"
echo -e "        Python Version    : ${BOLD}${PY_VER}${NC}"

# 3. Environment Variables for MPS Stability
echo -e "\n  [3/5] Configuring Apple Silicon Metal Environment..."
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

echo -e "        Set PYTORCH_ENABLE_MPS_FALLBACK=1 (guarantees seamless CPU fallback if niche op is needed)"
echo -e "        Set PYTHONPATH=${ROOT_DIR}"

# 4. Dependency & PyTorch MPS Acceleration Verification
echo -e "\n  [4/5] Testing PyTorch Metal Performance Shaders (MPS) Acceleration..."
python3 - <<'EOF'
import sys
import platform

try:
    import torch
except ImportError:
    print("\033[0;31m✘ PyTorch is not installed in the current environment.\033[0m")
    print("  Install with: pip install torch torchvision --upgrade")
    sys.exit(1)

print(f"        PyTorch Version   : {torch.__version__}")

mps_built = hasattr(torch.backends, "mps")
mps_available = mps_built and torch.backends.mps.is_available()

if mps_available:
    print(f"        MPS Metal Built   : \033[0;32m✔ True\033[0m")
    print(f"        MPS Available     : \033[0;32m✔ True (Apple Silicon GPU ACTIVE)\033[0m")
    try:
        # Benchmark quick matrix multiplication on MPS
        dev = torch.device("mps")
        x = torch.randn(1024, 1024, device=dev, dtype=torch.float32)
        y = torch.mm(x, x)
        torch.mps.synchronize()
        print(f"        MPS Tensor Test   : \033[0;32m✔ Successfully computed 1024x1024 matmul on {y.device}\033[0m")
    except Exception as e:
        print(f"        \033[1;33m⚠ Warning during MPS tensor allocation: {e}\033[0m")
else:
    print(f"        MPS Metal Built   : {mps_built}")
    print(f"        MPS Available     : \033[1;33m⚠ False\033[0m")
    if platform.system() == "Darwin":
        print("        Notice: MPS requires macOS 12.3+ and Apple Silicon (M1/M2/M3/M4).")
    print("        Fallback Device   : CPU")

EOF

# 5. Core Package Import Check
echo -e "\n  [5/5] Checking required scientific packages..."
python3 - <<'EOF'
packages = ["numpy", "pandas", "scipy", "sklearn", "joblib", "openpyxl", "pytest"]
missing = []
for pkg in packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"  \033[1;33m⚠ Missing packages: {missing}\033[0m")
    print(f"    Install missing dependencies: pip install {' '.join(missing)}")
else:
    print("  \033[0;32m✔ All required data science and ML packages are present.\033[0m")
EOF

# Completion Summary
echo -e "\n${BOLD}${CYAN}====================================================================${NC}"
echo -e "${BOLD}${GREEN}               Setup & Device Verification Complete!                ${NC}"
echo -e "${BOLD}${CYAN}====================================================================${NC}"
echo -e "\n${BOLD}Quick-Start Commands on Mac:${NC}"
echo -e "  1. Run unit tests:"
echo -e "     ${CYAN}./entrypoint.sh test${NC}"
echo -e "\n  2. Run a fast 1-round sanity check using GPU (MPS):
     ${CYAN}python3 main.py --mode centralized --feature_type dynamic --backbone hybrid_tcn_cnn --method replay --rounds_per_task 1 --allow_incomplete_benchmark --device mps${NC}

  3. Run the full benchmark suite (auto-detects Mac GPU):
     ${CYAN}python3 run_all.py --feature_type dynamic --allow_incomplete_benchmark${NC}
     ${YELLOW}(or pass --device mps explicitly)${NC}\n"
