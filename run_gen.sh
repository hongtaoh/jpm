#!/bin/bash
set -e  # Exit immediately on error

echo "run_gen.sh started at $(date)"
echo "Running in directory: $(pwd)"
echo "Running with arguments: $@"

# Prevent user-level site packages from interfering
export PYTHONNOUSERSITE=1

# ==============================================================================
# 📂 Prepare directories
# ==============================================================================
mkdir -p logs_gen
chmod 755 logs_gen
echo "Created logs directory at $(pwd)/logs_gen"

mkdir -p data
mkdir -p json_files


# ==============================================================================
# 🐍 Conda Env Extraction
# ==============================================================================
ENV_TARBALL="/staging/hhao9/ml4h.tar.gz"
ENV_DIR=".conda_env"
PYTHON_EXEC=""

rm -rf "$ENV_DIR" "$MINICONDA_DIR"

if [[ -f "$ENV_TARBALL" ]]; then
    echo "Extracting environment..."
    mkdir -p "$ENV_DIR"
    tar -xzf "$ENV_TARBALL" -C "$ENV_DIR"
    PYTHON_EXEC="$ENV_DIR/bin/python"
    echo "Using extracted environment at $PYTHON_EXEC"
else
    echo "⚠️ ml4h.tar.gz not found. Will attempt Miniconda setup if needed."
fi

# ==============================================================================
# 🧪 Final sanity check
# ==============================================================================
echo "=== ENVIRONMENT VALIDATION ==="
echo "Python path: $PYTHON_EXEC"
echo "Python version: $($PYTHON_EXEC --version)"

if ! "$PYTHON_EXEC" -c "import pyjpm, pyarrow, yaml;" &>/dev/null; then
    echo "❌ Final environment validation failed — aborting"
    exit 1
fi

# ==============================================================================
# ▶️ Run Python Script
# ==============================================================================
echo "=== STARTING MAIN SCRIPT ==="
"$PYTHON_EXEC" ./run_gen.py "$@"





echo "✅ Script completed at $(date)"
