#!/bin/bash
# Run tests via Docker

set -e

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "OPTIONS:"
    echo "  all         All tests"
    echo "  unit        Unit tests"
    echo "  integration Integration tests"
    echo "  coverage    With coverage"
    echo "  help        This help"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Docker not found"
        exit 1
    fi
}

run_tests() {
    local test_type=${1:-"all"}
    
    echo "Running tests: $test_type"
    
    # Ensure services are running
    docker compose up -d db redis
    
    case $test_type in
        "all")
            docker compose --profile test run --rm test python scripts/run_tests.py --coverage
            ;;
        "unit")
            docker compose --profile test run --rm test python scripts/run_tests.py --unit --coverage
            ;;
        "integration")
            docker compose --profile test run --rm test python scripts/run_tests.py --integration --coverage
            ;;
        "coverage")
            docker compose --profile test run --rm test python scripts/run_tests.py --coverage
            ;;
        "help")
            show_help
            exit 0
            ;;
        *)
            echo " Invalid option: $test_type"
            show_help
            exit 1
            ;;
    esac
}

# Main
check_docker
run_tests "$1"
echo " Tests completed!" 