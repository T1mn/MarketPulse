#!/bin/bash
# MarketPulse Deployment Script for Tencent Cloud CentOS 7
# Usage: ./scripts/deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root"
    exit 1
fi

DOMAIN="chat.tonwork.fun"
APP_DIR="/opt/marketpulse"

# =============================================================================
# Step 1: Install Docker
# =============================================================================
install_docker() {
    log_info "Installing Docker..."

    if command -v docker &> /dev/null; then
        log_info "Docker already installed"
        return
    fi

    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    systemctl start docker
    systemctl enable docker

    log_info "Docker installed successfully"
}

# =============================================================================
# Step 2: Install Nginx
# =============================================================================
install_nginx() {
    log_info "Installing Nginx..."

    if command -v nginx &> /dev/null; then
        log_info "Nginx already installed"
        return
    fi

    yum install -y epel-release
    yum install -y nginx

    systemctl enable nginx

    log_info "Nginx installed successfully"
}

# =============================================================================
# Step 3: Configure Firewall
# =============================================================================
configure_firewall() {
    log_info "Configuring firewall..."

    # Check if firewalld is running
    if ! systemctl is-active --quiet firewalld; then
        log_warn "firewalld is not running, skipping firewall configuration"
        return
    fi

    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload

    log_info "Firewall configured successfully"
}

# =============================================================================
# Step 4: Setup SSL Certificate
# =============================================================================
setup_ssl() {
    log_info "Setting up SSL certificate..."

    # Install certbot
    if ! command -v certbot &> /dev/null; then
        yum install -y certbot python3-certbot-nginx
    fi

    # Check if certificate already exists
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        log_info "SSL certificate already exists"
        return
    fi

    # Create webroot directory for ACME challenge
    mkdir -p /var/www/certbot

    # Get certificate (requires DNS to be configured first)
    log_warn "Make sure DNS is configured: $DOMAIN -> $(curl -s ifconfig.me)"
    read -p "Press Enter to continue with SSL certificate generation..."

    certbot certonly --webroot -w /var/www/certbot -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

    log_info "SSL certificate obtained successfully"
}

# =============================================================================
# Step 5: Setup Application
# =============================================================================
setup_app() {
    log_info "Setting up application..."

    # Create app directory
    mkdir -p $APP_DIR
    cd $APP_DIR

    # Create data directories
    mkdir -p data/core data/chroma

    # Check if .env exists
    if [ ! -f ".env" ]; then
        if [ -f ".env.production" ]; then
            cp .env.production .env
            log_warn "Created .env from .env.production - please edit with your credentials"
        else
            log_error ".env.production not found. Please upload the application files first."
            exit 1
        fi
    fi

    log_info "Application directory setup complete"
}

# =============================================================================
# Step 6: Build and Start Services
# =============================================================================
start_services() {
    log_info "Building and starting services..."

    cd $APP_DIR

    # Build Docker images
    docker compose build

    # Start services
    docker compose up -d

    # Wait for services to be healthy
    log_info "Waiting for services to start..."
    sleep 10

    # Check service status
    docker compose ps

    log_info "Services started successfully"
}

# =============================================================================
# Step 7: Configure Nginx
# =============================================================================
configure_nginx() {
    log_info "Configuring Nginx..."

    # Copy nginx config
    if [ -f "$APP_DIR/nginx/marketpulse.conf" ]; then
        cp $APP_DIR/nginx/marketpulse.conf /etc/nginx/conf.d/
    else
        log_error "Nginx config not found at $APP_DIR/nginx/marketpulse.conf"
        exit 1
    fi

    # Test nginx config
    nginx -t

    # Reload nginx
    systemctl reload nginx

    log_info "Nginx configured successfully"
}

# =============================================================================
# Step 8: Verify Deployment
# =============================================================================
verify_deployment() {
    log_info "Verifying deployment..."

    # Check local health
    if curl -sf http://localhost:3000/health > /dev/null; then
        log_info "Local health check: OK"
    else
        log_error "Local health check: FAILED"
    fi

    # Check HTTPS (if SSL is configured)
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        if curl -sf https://$DOMAIN/health > /dev/null; then
            log_info "HTTPS health check: OK"
        else
            log_warn "HTTPS health check: FAILED (DNS may not be propagated yet)"
        fi
    fi

    log_info "Deployment verification complete"
}

# =============================================================================
# Main
# =============================================================================
main() {
    log_info "Starting MarketPulse deployment..."
    log_info "Domain: $DOMAIN"
    log_info "App Directory: $APP_DIR"

    install_docker
    install_nginx
    configure_firewall
    setup_app
    start_services
    setup_ssl
    configure_nginx
    verify_deployment

    log_info "=========================================="
    log_info "Deployment complete!"
    log_info "=========================================="
    log_info "Access your application at: https://$DOMAIN"
    log_info ""
    log_info "Useful commands:"
    log_info "  docker compose logs -f server  # View server logs"
    log_info "  docker compose ps              # Check service status"
    log_info "  docker compose restart server  # Restart server"
    log_info ""
}

# Run main function
main "$@"
