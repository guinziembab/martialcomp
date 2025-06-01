#!/bin/bash
#
# MartialComp Tenant Backup Script
# Backs up all tenant data including schemas
#

set -e

# Configuration
BACKUP_DIR="/var/backups/martialcomp/tenants"
DB_NAME="martialcomp"
DB_USER="martialcomp_user"
DB_HOST="localhost"
MAX_BACKUPS=30  # Keep last 30 days of backups

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP"

echo -e "${GREEN}Starting MartialComp tenant backup...${NC}"

# Function to backup public schema
backup_public() {
    echo "Backing up public schema..."
    
    pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
        --schema=public \
        --file="${BACKUP_FILE}_public.sql" \
        --verbose
    
    # Compress
    gzip "${BACKUP_FILE}_public.sql"
    
    echo -e "${GREEN}✓ Public schema backed up${NC}"
}

# Function to backup tenant schemas
backup_tenants() {
    echo "Backing up tenant schemas..."
    
    # Get list of tenant schemas from database
    SCHEMAS=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'tenant_%'
    ")
    
    # Backup each tenant schema
    for schema in $SCHEMAS; do
        schema=$(echo $schema | xargs)  # Trim whitespace
        
        if [ ! -z "$schema" ]; then
            echo "  Backing up schema: $schema"
            
            pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
                --schema=$schema \
                --file="${BACKUP_FILE}_${schema}.sql" \
                --verbose
            
            # Compress
            gzip "${BACKUP_FILE}_${schema}.sql"
        fi
    done
    
    echo -e "${GREEN}✓ All tenant schemas backed up${NC}"
}

# Function to create metadata file
create_metadata() {
    echo "Creating backup metadata..."
    
    # Create metadata JSON
    cat > "${BACKUP_FILE}_metadata.json" <<EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -I)",
    "time": "$(date +%H:%M:%S)",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "schemas": [
        "public",
$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
    SELECT string_agg('        \"' || schema_name || '\"', ',\n')
    FROM information_schema.schemata 
    WHERE schema_name LIKE 'tenant_%'
")
    ],
    "tenant_count": $(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
        SELECT COUNT(*) 
        FROM public.multitenant_tenant
    "),
    "active_tenants": $(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
        SELECT COUNT(*) 
        FROM public.multitenant_tenant 
        WHERE is_active = true
    ")
}
EOF
    
    echo -e "${GREEN}✓ Metadata created${NC}"
}

# Function to create unified archive
create_archive() {
    echo "Creating unified backup archive..."
    
    cd $BACKUP_DIR
    
    # Create tar archive with all backup files
    tar -czf "martialcomp_backup_$TIMESTAMP.tar.gz" \
        $(ls backup_$TIMESTAMP* | grep -v ".tar.gz")
    
    # Remove individual files after archiving
    rm -f backup_$TIMESTAMP*.sql.gz
    rm -f backup_$TIMESTAMP*.json
    
    echo -e "${GREEN}✓ Backup archive created: martialcomp_backup_$TIMESTAMP.tar.gz${NC}"
}

# Function to cleanup old backups
cleanup_old_backups() {
    echo "Cleaning up old backups..."
    
    # Find and delete backups older than MAX_BACKUPS days
    find $BACKUP_DIR -name "martialcomp_backup_*.tar.gz" -mtime +$MAX_BACKUPS -delete
    
    echo -e "${GREEN}✓ Old backups cleaned up${NC}"
}

# Function to verify backup
verify_backup() {
    echo "Verifying backup..."
    
    ARCHIVE_FILE="$BACKUP_DIR/martialcomp_backup_$TIMESTAMP.tar.gz"
    
    if [ -f "$ARCHIVE_FILE" ]; then
        SIZE=$(du -h "$ARCHIVE_FILE" | cut -f1)
        echo -e "${GREEN}✓ Backup verified: $ARCHIVE_FILE ($SIZE)${NC}"
    else
        echo -e "${RED}✗ Backup verification failed!${NC}"
        exit 1
    fi
}

# Function to upload to S3 (optional)
upload_to_s3() {
    if [ ! -z "$S3_BUCKET" ]; then
        echo "Uploading to S3..."
        
        aws s3 cp "$BACKUP_DIR/martialcomp_backup_$TIMESTAMP.tar.gz" \
            "s3://$S3_BUCKET/backups/martialcomp_backup_$TIMESTAMP.tar.gz"
        
        echo -e "${GREEN}✓ Backup uploaded to S3${NC}"
    fi
}

# Main backup process
main() {
    backup_public
    backup_tenants
    create_metadata
    create_archive
    cleanup_old_backups
    verify_backup
    upload_to_s3
    
    echo -e "${GREEN}Backup completed successfully!${NC}"
}

# Check if PostgreSQL password is set
if [ -z "$PGPASSWORD" ]; then
    echo -e "${YELLOW}Warning: PGPASSWORD not set. You may be prompted for password.${NC}"
fi

# Run backup
main

# Exit successfully
exit 0