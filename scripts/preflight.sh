#!/bin/bash

# preflight.sh
# Runs local validation to ensure code is ready for push.
# Usage: ./scripts/preflight.sh [fast|full]

MODE=${1:-fast} # Default to fast mode

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Ensure we're in project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${CYAN}🚀 Starting Pre-Flight Validation ($MODE mode)...${NC}"

FAILED_STEPS=()

# Function to report status
report_status() {
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        echo -e "\n${GREEN}✅ PRE-FLIGHT CHECK PASSED! Ready for takeoff.${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ PRE-FLIGHT CHECK FAILED.${NC}"
        echo "Failed Steps:"
        for step in "${FAILED_STEPS[@]}"; do
            echo -e " - ${step}"
        done
        exit 1
    fi
}

# --- STEP 1: Python Syntax Check ---
echo -e "\n${YELLOW}[1/5] Checking Python Syntax...${NC}"
PYTHON_ERRORS=0
for pyfile in $(find backend/src -name "*.py" 2>/dev/null); do
    if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
        echo -e "${RED}     [FAIL] $pyfile${NC}"
        PYTHON_ERRORS=$((PYTHON_ERRORS + 1))
    fi
done
if [ $PYTHON_ERRORS -gt 0 ]; then
    FAILED_STEPS+=("Python Syntax ($PYTHON_ERRORS files)")
else
    echo -e "${GREEN}     [PASS] All Python files compile${NC}"
fi

# --- STEP 2: Local Linting ---
echo -e "\n${YELLOW}[2/5] Running Local Linters...${NC}"

# Backend Linting
echo "  -> Checking Backend (Ruff)..."
if command -v ruff &> /dev/null; then
    if ! ruff check backend/ 2>/dev/null; then
        echo -e "${RED}     [FAIL] Backend Linting${NC}"
        FAILED_STEPS+=("Backend Lint (Ruff)")
    else
        echo -e "${GREEN}     [PASS] Backend Linting${NC}"
    fi
else
    echo -e "${YELLOW}     [SKIP] Ruff not found (install with 'pip install ruff')${NC}"
fi

# Frontend Linting
echo "  -> Checking Frontend (ESLint)..."
if [ -d "frontend" ] && command -v npm &> /dev/null; then
    cd frontend
    if ! npm run lint --if-present -- --quiet 2>/dev/null; then
         echo -e "${RED}     [FAIL] Frontend Linting${NC}"
         FAILED_STEPS+=("Frontend Lint")
    else
         echo -e "${GREEN}     [PASS] Frontend Linting${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}     [SKIP] Frontend directory or npm not found${NC}"
fi

# --- STEP 3: Frontend Build Check ---
echo -e "\n${YELLOW}[3/5] Checking Frontend Build...${NC}"
if [ -d "frontend" ] && command -v npm &> /dev/null; then
    cd frontend
    if ! npm run build 2>&1 | tail -5; then
        echo -e "${RED}     [FAIL] Frontend Build${NC}"
        FAILED_STEPS+=("Frontend Build")
    else
        echo -e "${GREEN}     [PASS] Frontend Build${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}     [SKIP] Frontend directory or npm not found${NC}"
fi

# --- STEP 4: Docker Build Check (fast: skip, full: build) ---
if [ "$MODE" == "full" ]; then
    echo -e "\n${YELLOW}[4/5] Checking Docker Build...${NC}"
    if command -v docker &> /dev/null; then
        if docker build -t preflight-check . --quiet 2>&1 | tail -3; then
            echo -e "${GREEN}     [PASS] Docker Build${NC}"
            docker rmi preflight-check --force &>/dev/null
        else
            echo -e "${RED}     [FAIL] Docker Build${NC}"
            FAILED_STEPS+=("Docker Build")
        fi
    else
        echo -e "${YELLOW}     [SKIP] Docker not found${NC}"
    fi
else
    echo -e "\n${YELLOW}[4/5] Skipping Docker Build (Use './scripts/preflight.sh full')${NC}"
fi

# --- STEP 5: CI Simulation (Full Mode ONLY) ---
if [ "$MODE" == "full" ]; then
    echo -e "\n${YELLOW}[5/5] Simulating GitHub Actions (using act)...${NC}"
    
    # Check for secrets file
    SECRETS_ARG=""
    if [ -f ".secrets" ]; then
        SECRETS_ARG="--secret-file .secrets"
    elif [ -f ".env" ]; then
         echo -e "${YELLOW}     Note: Using .env for secrets${NC}"
         SECRETS_ARG="--env-file .env"
    fi

    echo "  -> Running CI Pipeline..."
    if command -v act &> /dev/null; then
        if act -W .github/workflows/ci-orchestrator.yml $SECRETS_ARG --rm 2>&1 | tail -10; then
            echo -e "${GREEN}     [PASS] CI Simulation${NC}"
        else
            echo -e "${RED}     [FAIL] CI Simulation${NC}"
            FAILED_STEPS+=("GitHub Actions Simulation (act)")
        fi
    else
        echo -e "${YELLOW}     [SKIP] 'act' not found (install from https://github.com/nektos/act)${NC}"
    fi
else
    echo -e "\n${YELLOW}[5/5] Skipping CI Simulation (Use './scripts/preflight.sh full')${NC}"
fi

# --- Final Report ---
report_status

