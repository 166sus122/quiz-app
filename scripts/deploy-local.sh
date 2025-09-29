#!/bin/bash

# סקריפט פריסה מקומית לבדיקת CI/CD
# מדמה את תהליך הפריסה שיתרחש בייצור

set -e

# צבעים לפלט
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# פונקציות עזר
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# בדיקת dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    log_success "All dependencies are available"
}

# בניית images מקומית
build_images() {
    log_info "Building local images..."

    services=("nginx" "auth-service" "quiz-app" "fail2ban")

    for service in "${services[@]}"; do
        log_info "Building $service..."
        docker build -t "dov121212/quiz-app-$service:local" "./$service"
    done

    log_success "All images built successfully"
}

# עדכון docker-compose לשימוש בtags מקומיים
prepare_local_compose() {
    log_info "Preparing docker-compose for local deployment..."

    cp docker-compose.prod.yml docker-compose.local.yml

    # החלפת :latest ב-:local
    sed -i 's/:latest/:local/g' docker-compose.local.yml

    log_success "Local compose file ready"
}

# הפעלת הסטק
deploy_stack() {
    log_info "Deploying the stack..."

    # עצירת סטק קיים
    docker-compose -f docker-compose.local.yml down -v 2>/dev/null || true

    # ניקוי
    docker system prune -f >/dev/null 2>&1 || true

    # הפעלה
    docker-compose -f docker-compose.local.yml up -d

    log_success "Stack deployed"
}

# בדיקת health של השירותים
check_health() {
    log_info "Checking service health..."

    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/login >/dev/null 2>&1; then
            log_success "Services are healthy!"
            return 0
        fi

        log_info "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "Services failed to become healthy"
    return 1
}

# הרצת בדיקות smoke
run_smoke_tests() {
    log_info "Running smoke tests..."

    # בדיקת דף login
    if curl -f http://localhost/login | grep -q "אפליקציית חידות"; then
        log_success "✅ Login page accessible"
    else
        log_error "❌ Login page not accessible"
        return 1
    fi

    # בדיקת API (צריך להחזיר שגיאה ללא אימות)
    if curl -f http://localhost/api/question 2>/dev/null | grep -q "error"; then
        log_success "✅ API responding correctly"
    else
        log_error "❌ API not responding correctly"
        return 1
    fi

    # בדיקת התחברות מלאה
    if test_login; then
        log_success "✅ Full login flow working"
    else
        log_error "❌ Login flow failed"
        return 1
    fi

    log_success "All smoke tests passed!"
}

# בדיקת זרימת התחברות
test_login() {
    local cookie_file="/tmp/deploy_test_cookie.txt"

    # ניסיון התחברות
    if curl -c "$cookie_file" -X POST -d "username=admin&password=admin123" \
        http://localhost/auth 2>/dev/null | grep -q "Redirecting"; then

        # בדיקת session
        if curl -b "$cookie_file" http://localhost/verify 2>/dev/null | grep -q "authenticated"; then
            rm -f "$cookie_file"
            return 0
        fi
    fi

    rm -f "$cookie_file"
    return 1
}

# הצגת סטטוס
show_status() {
    log_info "Current deployment status:"
    echo
    docker-compose -f docker-compose.local.yml ps
    echo

    log_info "Service logs (last 10 lines each):"
    services=("quiz-nginx-prod" "quiz-auth-prod" "quiz-app-prod" "quiz-fail2ban-prod")

    for service in "${services[@]}"; do
        echo -e "\n${BLUE}=== $service ===${NC}"
        docker logs --tail 10 "$service" 2>/dev/null || echo "Service not running"
    done
}

# ניקוי
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f docker-compose.local.yml down -v >/dev/null 2>&1 || true
    docker system prune -f >/dev/null 2>&1 || true
    rm -f docker-compose.local.yml
    log_success "Cleanup completed"
}

# פונקציית עזרה
show_help() {
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  deploy     - Full deployment (default)"
    echo "  build      - Build images only"
    echo "  test       - Run tests only"
    echo "  status     - Show current status"
    echo "  cleanup    - Clean up everything"
    echo "  help       - Show this help"
    echo
    echo "Examples:"
    echo "  $0          # Full deployment"
    echo "  $0 build    # Build images only"
    echo "  $0 test     # Test current deployment"
}

# Main execution
main() {
    local command=${1:-deploy}

    case $command in
        "build")
            check_dependencies
            build_images
            ;;
        "deploy")
            log_info "Starting local deployment simulation..."
            check_dependencies
            build_images
            prepare_local_compose
            deploy_stack

            if check_health; then
                run_smoke_tests
                show_status
                log_success "🎉 Local deployment completed successfully!"
                log_info "Access the app at: http://localhost"
                log_info "Use 'docker-compose -f docker-compose.local.yml logs -f' to follow logs"
            else
                log_error "Deployment failed - showing logs:"
                show_status
                exit 1
            fi
            ;;
        "test")
            if check_health; then
                run_smoke_tests
            else
                log_error "Services are not healthy"
                exit 1
            fi
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Trap for cleanup on script exit
trap 'if [ $? -ne 0 ]; then log_error "Script failed - check logs above"; fi' EXIT

# Run main function
main "$@"