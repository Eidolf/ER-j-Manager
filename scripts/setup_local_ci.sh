#!/bin/bash

# setup_local_ci.sh
# Ensures that necessary tools (act, docker) are available for local pre-flight checks.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[*] Auditing Local CI Environment...${NC}"

# 1. Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[X] Docker is not installed.${NC}"
    echo "    Please install Docker Desktop or Docker Engine: https://docs.docker.com/get-docker/"
    exit 1
fi
if ! docker info &> /dev/null; then
    echo -e "${RED}[X] Docker daemon is not running.${NC}"
    echo "    Please start Docker."
    exit 1
fi
echo -e "${GREEN}[V] Docker is ready.${NC}"

# 2. Check Act
if ! command -v act &> /dev/null; then
    echo -e "${YELLOW}[!] 'act' is not installed.${NC}"
    echo "    Attempting installation..."
    # Basic install for easy cases; user might need manual install if this fails/is not preferred
    if curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash; then
         echo -e "${GREEN}[V] 'act' installed successfully.${NC}"
    else
         echo -e "${RED}[X] Failed to install 'act'.${NC}"
         echo "    Please install strictly: https://nektos-act.com/installation/index"
         exit 1
    fi
else
    echo -e "${GREEN}[V] 'act' is installed ($(act --version | head -n1)).${NC}"
fi

# 3. Check Language Runtimes (Basic Check)
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[!] Python 3 not found. Some local linters may fail.${NC}"
fi
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}[!] npm not found. Frontend checks may fail.${NC}"
fi

echo -e "${GREEN}[*] Environment Ready! You can now run './scripts/preflight.sh'${NC}"
