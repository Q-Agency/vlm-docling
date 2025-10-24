#!/usr/bin/env bash
set -euo pipefail

# ---- config ----
SERVICE_NAME="${SERVICE_NAME:-vlm-docling}"

# choose compose command (prefers v2 plugin)
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
  COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose"
else
  echo "❌ Docker Compose not found. Install docker compose v2 (docker-compose-plugin)." >&2
  exit 1
fi

NO_CACHE="false"
PULL="true"
FORCE_RECREATE="true"
DETACHED="true"

usage() {
  cat <<EOF
Usage: $0 [--no-cache] [--no-pull] [--no-recreate] [--detached] [--foreground]

Options:
  --no-cache      Build without cache (slow, clean rebuild)
  --no-pull       Skip 'git pull'
  --no-recreate   Don't force container recreation
  --detached      Run in background (default)
  --foreground    Run attached (see logs inline)
  -h, --help      Show this help
EOF
}

# parse args
for arg in "$@"; do
  case "$arg" in
    --no-cache) NO_CACHE="true" ;;
    --no-pull) PULL="false" ;;
    --no-recreate) FORCE_RECREATE="false" ;;
    --detached) DETACHED="true" ;;
    --foreground) DETACHED="false" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

echo "🔧 Using compose command: $COMPOSE"
echo "🔧 Service: $SERVICE_NAME"
echo

# 1) pull latest repo
if [[ "$PULL" == "true" ]]; then
  echo "⬇️  git pull"
  git pull --ff-only
  echo
fi

# 2) remove existing container (keep volumes)
if docker ps -a --format '{{.Names}}' | grep -qx "$SERVICE_NAME"; then
  echo "🗑️  Removing existing container '$SERVICE_NAME' (volumes preserved)"
  docker rm -f "$SERVICE_NAME" >/dev/null || true
  echo
fi

# 3) build (optionally no-cache)
echo "🏗️  Building image"
if [[ "$NO_CACHE" == "true" ]]; then
  $COMPOSE build --no-cache
else
  $COMPOSE build
fi
echo

# 4) up (detached or foreground, optionally force recreate)
echo "🚀 Starting containers"
UP_FLAGS=()
if [[ "$FORCE_RECREATE" == "true" ]]; then
  UP_FLAGS+=(--force-recreate)
fi
if [[ "$DETACHED" == "true" ]]; then
  UP_FLAGS+=(-d)
fi

$COMPOSE up "${UP_FLAGS[@]}"

echo
echo "✅ Done. Logs:  $COMPOSE logs -f $SERVICE_NAME"
