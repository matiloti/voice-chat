#!/usr/bin/env bash
# Voice Chat — one-command launcher
# Creates venvs, installs deps, and starts both backend + frontend.
#
# Usage:
#   ./run.sh          Start everything
#   ./run.sh backend  Start backend only
#   ./run.sh frontend Start frontend only

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[info]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ok]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
error() { echo -e "${RED}[error]${NC} $*" >&2; }

# ---- Pre-flight checks ----

check_python() {
    if ! command -v python3 &>/dev/null; then
        error "python3 not found. Install with: brew install python@3.12"
        exit 1
    fi
    local ver
    ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    if (( major < 3 || (major == 3 && minor < 11) )); then
        error "Python 3.11+ required (found $ver). Install with: brew install python@3.12"
        exit 1
    fi
    ok "Python $ver"
}

check_node() {
    if ! command -v node &>/dev/null; then
        error "node not found. Install with: brew install node"
        exit 1
    fi
    local ver
    ver=$(node --version | tr -d 'v')
    local major
    major=$(echo "$ver" | cut -d. -f1)
    if (( major < 18 )); then
        error "Node.js 18+ required (found $ver). Install with: brew install node"
        exit 1
    fi
    ok "Node.js $ver"
}

check_env() {
    if [ ! -f "$ROOT_DIR/.env" ]; then
        warn ".env not found — copying from .env.example"
        cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
        warn "Edit .env to set your BRAVE_SEARCH_API_KEY (optional but recommended)"
    else
        ok ".env found"
    fi
}

# ---- Backend (Python venv) ----

setup_backend() {
    info "Setting up backend..."

    # Create venv if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        info "Creating Python virtual environment at backend/.venv ..."
        python3 -m venv "$VENV_DIR"
        ok "Virtual environment created"
    else
        ok "Virtual environment exists"
    fi

    # Activate venv
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    # Install/update deps if needed
    # We check if the package is installed; if not, install it.
    if ! python3 -c "import fastapi" &>/dev/null; then
        info "Installing Python dependencies (first time takes 2-5 min)..."
        pip install -e "$BACKEND_DIR" --quiet
        ok "Python dependencies installed"
    else
        ok "Python dependencies already installed"
    fi
}

start_backend() {
    setup_backend
    info "Starting backend on http://localhost:8000 ..."
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    exec uvicorn main:app --host 0.0.0.0 --port 8000
}

start_backend_bg() {
    setup_backend
    info "Starting backend on http://localhost:8000 (background)..."
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    uvicorn main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    # Wait for the server to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health &>/dev/null; then
            ok "Backend running (PID $BACKEND_PID)"
            return 0
        fi
        sleep 0.5
    done
    warn "Backend started but health check timed out — it may still be loading"
}

# ---- Frontend ----

setup_frontend() {
    info "Setting up frontend..."

    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        info "Installing npm dependencies..."
        cd "$FRONTEND_DIR"
        npm install --silent
        ok "npm dependencies installed"
    else
        ok "npm dependencies already installed"
    fi
}

start_frontend() {
    setup_frontend
    info "Starting frontend on http://localhost:5173 ..."
    cd "$FRONTEND_DIR"
    exec npm run dev
}

# ---- Cleanup on exit ----

cleanup() {
    if [ -n "${BACKEND_PID:-}" ]; then
        info "Stopping backend (PID $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
}

# ---- Main ----

main() {
    local mode="${1:-all}"

    echo ""
    echo -e "${CYAN}Voice Chat${NC}"
    echo "=========="
    echo ""

    case "$mode" in
        backend)
            check_python
            check_env
            start_backend
            ;;
        frontend)
            check_node
            start_frontend
            ;;
        all)
            check_python
            check_node
            check_env

            trap cleanup EXIT INT TERM

            start_backend_bg
            echo ""
            start_frontend
            ;;
        *)
            echo "Usage: $0 [backend|frontend|all]"
            exit 1
            ;;
    esac
}

main "$@"
