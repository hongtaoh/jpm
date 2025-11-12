#!/bin/bash
set -e  # Exit immediately on error

echo "run_mlhc.sh started at $(date)"
echo "Running in directory: $(pwd)"
echo "Running with arguments: $@"

# Prevent user-level site packages from interfering
export PYTHONNOUSERSITE=1

# ==============================================================================
# 📂 Prepare directories
# ==============================================================================
mkdir -p logs
chmod 755 logs
echo "Created logs directory at $(pwd)/logs"

# data dir -> algo 
for dir1 in BT PL PL Mallows_Tau_T1 Mallows_Tau_T10 Pairwise Random; do 
    for dir in saebm Pairwise BT PL Mallows_Tau; do
        mkdir -p "algo_results/$dir1/$dir"
    done
done

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
# 📦 Extract data
# ==============================================================================
DATA_TARBALL="/staging/hhao9/mpebm_data.tar.gz"

if [[ -f "$DATA_TARBALL" ]]; then
    echo "📦 Extracting $DATA_TARBALL..."
    tar -xzf "$DATA_TARBALL"
    # If extraction creates "mpebm_data", rename to "data"
    if [[ -d "mpebm_data" ]]; then
        rm -rf data   # remove old data folder if it exists
        mv mpebm_data data
        echo "Renamed mpebm_data -> data"
    fi
else
    echo "❌ $DATA_TARBALL not found — aborting"
    exit 1
fi

# # data*.tar.gz matches data.tar.gz, data0.tar.gz, data1.tar.gz, etc.
# for file in data*.tar.gz; do
#     if [[ -f "$file" ]]; then
#         echo "📦 Extracting $file..."
#         tar -xzf "$file" || echo "❗ Extraction failed for $file"
#     else
#         echo "⚠️ $file not found. Skipping."
#     fi
# done


# ==============================================================================
# See files present
# ==============================================================================
# echo "Files present:"
# ls -l

# ==============================================================================
# ▶️ Run Python Script
# ==============================================================================
echo "=== STARTING MAIN SCRIPT ==="
"$PYTHON_EXEC" ./run_mlhc.py "$@"

echo "✅ Script completed at $(date)"
