#!/usr/bin/env bash
# deploy.sh — Production deploy script for the Garage web app.
#
# Runs on the Raspberry Pi (either via GitHub Actions self-hosted runner or
# manually via SSH).  Handles code update, dependency sync, database migrations,
# service restart, health check, and automatic rollback on failure.
#
# Usage:
#   cd /opt/garage/app && bash deploy.sh

set -euo pipefail

APP_DIR="/opt/garage/app"
BACKUP_DIR="/opt/garage/backups"
DEPLOY_LOG="/opt/garage/deploy.log"
HEALTH_URL="http://127.0.0.1:5000/login"
HEALTH_RETRIES=10
HEALTH_DELAY=3

# State variables (populated during pre_deploy)
PREV_COMMIT=""
DB_BACKUP_FILE=""

# ── Helpers ──────────────────────────────────────────────────────────────────

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DEPLOY_LOG"; }

read_env() {
    # Read a key from the .env file.  Usage: read_env DB_USER
    grep "^${1}=" "$APP_DIR/.env" | cut -d '=' -f2-
}

# ── Pre-deploy ───────────────────────────────────────────────────────────────

pre_deploy() {
    log "=== PRE-DEPLOY ==="
    cd "$APP_DIR"

    # Record current commit for rollback
    PREV_COMMIT=$(git rev-parse HEAD)
    log "Current commit: $PREV_COMMIT"

    # Database backup
    mkdir -p "$BACKUP_DIR"
    local date_stamp
    date_stamp=$(date +%Y%m%d_%H%M%S)
    DB_BACKUP_FILE="$BACKUP_DIR/db_deploy_${date_stamp}.sql"

    local db_user db_pass db_name
    db_user=$(read_env DB_USER)
    db_pass=$(read_env DB_PASSWORD)
    db_name=$(read_env DB_NAME)

    log "Backing up database $db_name -> $DB_BACKUP_FILE"
    mysqldump -u "$db_user" -p"$db_pass" "$db_name" > "$DB_BACKUP_FILE"
    log "Database backup complete ($(du -h "$DB_BACKUP_FILE" | cut -f1))"
}

# ── Deploy ───────────────────────────────────────────────────────────────────

deploy() {
    log "=== DEPLOY ==="
    cd "$APP_DIR"

    # Pull latest code
    log "Fetching latest code from origin/main..."
    git fetch origin main
    git reset --hard origin/main

    local new_commit
    new_commit=$(git rev-parse HEAD)
    log "Deployed commit: $new_commit"

    if [ "$new_commit" = "$PREV_COMMIT" ]; then
        log "No new commits to deploy — continuing anyway (deps/migrations may have changed)"
    fi

    # Sync dependencies
    log "Syncing dependencies with uv..."
    uv sync --frozen
    log "Dependencies synced"

    # Run all migration scripts (each is idempotent)
    log "Running database migrations..."
    for migration in migrate_db.py migrate_rbac.py migrate_api_key.py migrate_sms_notifications.py; do
        if [ -f "$APP_DIR/$migration" ]; then
            log "  Running $migration"
            uv run python "$migration"
        fi
    done
    log "Migrations complete"
}

# ── Post-deploy ──────────────────────────────────────────────────────────────

post_deploy() {
    log "=== POST-DEPLOY ==="

    # Restart the service
    log "Restarting garage.service..."
    sudo systemctl restart garage.service
    log "Service restarted, running health check..."

    # Health check with retries
    local attempt=0
    while [ $attempt -lt $HEALTH_RETRIES ]; do
        attempt=$((attempt + 1))
        sleep "$HEALTH_DELAY"
        if timeout 5 curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
            log "Health check passed (attempt $attempt/$HEALTH_RETRIES)"
            return 0
        fi
        log "Health check attempt $attempt/$HEALTH_RETRIES failed"
    done

    log "ERROR: Health check failed after $HEALTH_RETRIES attempts"
    return 1
}

# ── Rollback ─────────────────────────────────────────────────────────────────

rollback() {
    log "!!! ROLLBACK INITIATED !!!"
    cd "$APP_DIR"

    # Revert code to previous commit
    if [ -n "$PREV_COMMIT" ]; then
        log "Reverting to commit $PREV_COMMIT"
        git reset --hard "$PREV_COMMIT"
        uv sync --frozen
    fi

    # Restore database from pre-deploy backup
    if [ -n "$DB_BACKUP_FILE" ] && [ -f "$DB_BACKUP_FILE" ]; then
        local db_user db_pass db_name
        db_user=$(read_env DB_USER)
        db_pass=$(read_env DB_PASSWORD)
        db_name=$(read_env DB_NAME)

        log "Restoring database from $DB_BACKUP_FILE"
        mysql -u "$db_user" -p"$db_pass" "$db_name" < "$DB_BACKUP_FILE"
    fi

    # Restart service with previous version
    log "Restarting service with previous version..."
    sudo systemctl restart garage.service
    sleep 5

    if timeout 5 curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        log "Rollback successful — service is healthy on previous version"
    else
        log "CRITICAL: Rollback health check also failed — manual intervention required"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
    log "========================================="
    log "DEPLOY STARTED"
    log "========================================="

    pre_deploy

    if deploy && post_deploy; then
        log "========================================="
        log "DEPLOY SUCCEEDED"
        log "========================================="

        # Housekeeping: keep only the last 10 deploy backups
        ls -1t "$BACKUP_DIR"/db_deploy_*.sql 2>/dev/null | tail -n +11 | xargs -r rm
        exit 0
    else
        rollback
        log "========================================="
        log "DEPLOY FAILED — ROLLED BACK"
        log "========================================="
        exit 1
    fi
}

main "$@"
