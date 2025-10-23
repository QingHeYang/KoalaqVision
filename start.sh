#!/bin/bash
set -e

# ============================================================
# KoalaqVision Service Manager
# ============================================================

# 颜色定义
RED=$'\e[0;31m'
GREEN=$'\e[0;32m'
YELLOW=$'\e[1;33m'
BLUE=$'\e[0;34m'
CYAN=$'\e[0;36m'
WHITE=$'\e[1;37m'
NC=$'\e[0m'
BOLD=$'\e[1m'

# 配置
PID_FILE=".koalaq.pid"
LOG_FILE="koalaq.log"
PYTHON_CMD="python"
WEAVIATE_COMPOSE="deploy/docker-compose.weaviate.yml"
WEAVIATE_CONTAINER="koalaq-weaviate-standalone"
WEAVIATE_PORT="10769"

# 打印标题
print_header() {
    clear
    echo "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${WHITE}          KoalaqVision Service Manager                   ${CYAN}║${NC}"
    echo "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 打印分隔线
print_separator() {
    echo "${BLUE}────────────────────────────────────────────────────────────${NC}"
}

# 打印成功消息
print_success() {
    echo "${GREEN}✓${NC} $1"
}

# 打印错误消息
print_error() {
    echo "${RED}✗${NC} $1"
}

# 打印警告消息
print_warning() {
    echo "${YELLOW}⚠${NC} $1"
}

# 打印信息消息
print_info() {
    echo "${CYAN}ℹ${NC} $1"
}

# 加载配置
load_config() {
    if [ -f .env ]; then
        # 加载全部环境变量（排除注释和空行）
        set -a
        source .env
        set +a
    fi

    API_PORT=${API_PORT:-10770}
    API_HOST=${API_HOST:-0.0.0.0}
    APP_MODE=${APP_MODE:-object}
}

# 获取本机所有IP地址
get_local_ips() {
    # 获取所有非loopback的IPv4地址
    ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' || true

    # 如果没有获取到，尝试hostname -I
    if [ -z "$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1')" ]; then
        hostname -I 2>/dev/null | tr ' ' '\n' | grep -v '127.0.0.1' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' || true
    fi
}

# 显示访问地址
show_access_urls() {
    local protocol="http"
    if [ "${ENABLE_SSL}" = "true" ]; then
        protocol="https"
    fi

    echo ""
    print_separator
    echo "${BOLD}Access URLs:${NC}"
    print_separator
    echo ""

    # 本地地址
    echo "${GREEN}Local:${NC}"
    echo "  ${CYAN}→${NC} ${protocol}://localhost:${API_PORT}"
    echo "  ${CYAN}→${NC} ${protocol}://127.0.0.1:${API_PORT}"
    echo ""

    # 网络地址
    local ips=($(get_local_ips))
    if [ ${#ips[@]} -gt 0 ]; then
        echo "${GREEN}Network:${NC}"
        for ip in "${ips[@]}"; do
            echo "  ${CYAN}→${NC} ${protocol}://${ip}:${API_PORT}"
        done
        echo ""
    fi

    # UI地址
    echo "${GREEN}Web UI:${NC}"
    echo "  ${CYAN}→${NC} ${protocol}://localhost:${API_PORT}/ui"
    if [ ${#ips[@]} -gt 0 ]; then
        for ip in "${ips[@]}"; do
            echo "  ${CYAN}→${NC} ${protocol}://${ip}:${API_PORT}/ui"
        done
    fi
    echo ""

    # API文档
    echo "${GREEN}API Docs:${NC}"
    echo "  ${CYAN}→${NC} ${protocol}://localhost:${API_PORT}/docs"
    echo "  ${CYAN}→${NC} ${protocol}://localhost:${API_PORT}/redoc"
    echo ""

    print_separator
}

# 检查服务是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID文件存在但进程已死，清理PID文件
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 获取服务状态
get_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        local uptime=$(ps -p "$pid" -o etime= 2>/dev/null | tr -d ' ')
        echo "${GREEN}Running${NC} (PID: ${pid}, Uptime: ${uptime})"
        return 0
    else
        # 检查端口是否被占用
        local port_pid=$(lsof -ti:$API_PORT 2>/dev/null || true)
        if [ ! -z "$port_pid" ]; then
            echo "${YELLOW}Unknown${NC} (Port ${API_PORT} occupied by PID: ${port_pid})"
            return 2
        else
            echo "${RED}Stopped${NC}"
            return 1
        fi
    fi
}

# 检查 Weaviate 是否运行
is_weaviate_running() {
    if docker ps --filter "name=$WEAVIATE_CONTAINER" --filter "status=running" --format "{{.Names}}" | grep -q "$WEAVIATE_CONTAINER"; then
        return 0
    else
        return 1
    fi
}

# 检查 Weaviate 健康状态
check_weaviate_health() {
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "http://localhost:$WEAVIATE_PORT/v1/.well-known/ready" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        ((attempt++))
    done

    return 1
}

# 启动 Weaviate
start_weaviate() {
    if is_weaviate_running; then
        print_success "Weaviate is already running"
        return 0
    fi

    if [ ! -f "$WEAVIATE_COMPOSE" ]; then
        print_error "Weaviate compose file not found: $WEAVIATE_COMPOSE"
        return 1
    fi

    print_info "Starting Weaviate vector database..."

    if docker compose -f "$WEAVIATE_COMPOSE" up -d; then
        print_success "Weaviate container started"

        print_info "Waiting for Weaviate to be ready..."
        if check_weaviate_health; then
            print_success "Weaviate is ready!"
            return 0
        else
            print_error "Weaviate failed to become healthy"
            return 1
        fi
    else
        print_error "Failed to start Weaviate"
        return 1
    fi
}

# 获取 Weaviate 状态
get_weaviate_status() {
    if is_weaviate_running; then
        echo "${GREEN}Running${NC}"
        return 0
    else
        echo "${RED}Stopped${NC}"
        return 1
    fi
}

# 停止 Weaviate
stop_weaviate() {
    if is_weaviate_running; then
        print_info "Stopping Weaviate..."
        if docker compose -f "$WEAVIATE_COMPOSE" down; then
            print_success "Weaviate stopped"
        else
            print_warning "Failed to stop Weaviate gracefully, trying force stop..."
            docker stop "$WEAVIATE_CONTAINER" 2>/dev/null || true
        fi
    fi
}

# 停止服务
stop_service() {
    print_separator
    print_info "Stopping KoalaqVision..."
    print_separator
    echo ""

    local stopped=false

    # 从PID文件停止
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_info "Stopping process (PID: ${pid})..."
            kill "$pid" 2>/dev/null || true

            # 等待进程结束
            for i in {1..10}; do
                if ! ps -p "$pid" > /dev/null 2>&1; then
                    break
                fi
                sleep 0.5
            done

            # 如果还没结束，强制杀死
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Process not responding, force killing..."
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi

            stopped=true
        fi
        rm -f "$PID_FILE"
    fi

    # 杀死端口占用进程
    local port_pid=$(lsof -ti:$API_PORT 2>/dev/null || true)
    if [ ! -z "$port_pid" ]; then
        print_info "Killing process on port ${API_PORT} (PID: ${port_pid})..."
        kill -9 "$port_pid" 2>/dev/null || true
        sleep 1
        stopped=true
    fi

    # 清理所有相关进程
    if pkill -9 -f "uvicorn app.main:app" 2>/dev/null; then
        stopped=true
    fi
    if pkill -9 -f "python.*app.main" 2>/dev/null; then
        stopped=true
    fi

    if [ "$stopped" = true ]; then
        print_success "Service stopped"
    else
        print_info "Service was not running"
    fi

    # 停止 Weaviate
    echo ""
    stop_weaviate

    echo ""
}

# 启动服务（后台）
start_background() {
    print_header
    echo "${BOLD}Start Service (Background Mode)${NC}"

    load_config

    # 检查是否已运行
    if is_running; then
        echo ""
        print_warning "Service is already running!"
        local pid=$(cat "$PID_FILE")
        print_info "PID: ${pid}"
        echo ""
        read -p "${YELLOW}Do you want to restart? [y/N]: ${NC}" confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            return
        fi
        stop_service
    fi

    echo ""
    print_info "Configuration:"
    echo "  ${CYAN}→${NC} Host: ${API_HOST}"
    echo "  ${CYAN}→${NC} Port: ${API_PORT}"
    echo "  ${CYAN}→${NC} Mode: ${APP_MODE}"
    echo "  ${CYAN}→${NC} Log: ${LOG_FILE}"
    echo ""

    # 启动 Weaviate
    print_separator
    if ! start_weaviate; then
        print_error "Cannot start service without Weaviate"
        read -p "Press Enter to continue..."
        return 1
    fi
    print_separator
    echo ""

    print_separator
    print_info "Starting service in background..."
    print_separator
    echo ""

    # 启动服务
    nohup $PYTHON_CMD -m app.main > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    # 等待服务启动
    sleep 2

    # 检查是否启动成功
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "Service started successfully!"
        print_info "PID: ${pid}"

        show_access_urls

        echo "${CYAN}View logs:${NC}"
        echo "  ${YELLOW}→${NC} tail -f $LOG_FILE"
        echo "  ${YELLOW}→${NC} ./start.sh logs"
        echo ""
    else
        print_error "Failed to start service"
        rm -f "$PID_FILE"
        echo ""
        print_info "Check logs:"
        echo "  tail -50 $LOG_FILE"
        echo ""
    fi

    read -p "Press Enter to continue..."
}

# 启动服务（前台）
start_foreground() {
    print_header
    echo "${BOLD}Start Service (Foreground Mode)${NC}"

    load_config

    # 检查是否已运行
    if is_running; then
        echo ""
        print_warning "Service is already running in background!"
        local pid=$(cat "$PID_FILE")
        print_info "PID: ${pid}"
        echo ""
        read -p "${YELLOW}Stop background service and start in foreground? [y/N]: ${NC}" confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            return
        fi
        stop_service
    fi

    echo ""
    print_info "Configuration:"
    echo "  ${CYAN}→${NC} Host: ${API_HOST}"
    echo "  ${CYAN}→${NC} Port: ${API_PORT}"
    echo "  ${CYAN}→${NC} Mode: ${APP_MODE}"
    echo ""

    # 启动 Weaviate
    print_separator
    if ! start_weaviate; then
        print_error "Cannot start service without Weaviate"
        return 1
    fi
    print_separator

    show_access_urls

    print_separator
    print_info "Starting service in foreground..."
    print_info "Press Ctrl+C to stop"
    print_separator
    echo ""

    sleep 2

    # 启动服务（前台）
    $PYTHON_CMD -m app.main
}

# 重启服务
restart_service() {
    print_header
    echo "${BOLD}Restart Service${NC}"

    load_config

    if ! is_running; then
        echo ""
        print_warning "Service is not running"
        echo ""
        read -p "${YELLOW}Start service? [y/N]: ${NC}" confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    echo ""
    stop_service

    sleep 1

    # 启动 Weaviate
    print_separator
    if ! start_weaviate; then
        print_error "Cannot start service without Weaviate"
        read -p "Press Enter to continue..."
        return 1
    fi
    print_separator
    echo ""

    print_separator
    print_info "Starting service..."
    print_separator
    echo ""

    # 启动服务
    nohup $PYTHON_CMD -m app.main > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    # 等待服务启动
    sleep 2

    # 检查是否启动成功
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "Service restarted successfully!"
        print_info "PID: ${pid}"

        show_access_urls
    else
        print_error "Failed to restart service"
        rm -f "$PID_FILE"
        echo ""
        print_info "Check logs:"
        echo "  tail -50 $LOG_FILE"
        echo ""
    fi

    read -p "Press Enter to continue..."
}

# 查看服务状态
show_status() {
    print_header
    echo "${BOLD}Service Status${NC}"
    print_separator
    echo ""

    load_config

    echo "${BOLD}Configuration:${NC}"
    echo "  ${CYAN}→${NC} Host: ${API_HOST}"
    echo "  ${CYAN}→${NC} Port: ${API_PORT}"
    echo "  ${CYAN}→${NC} Mode: ${APP_MODE}"
    echo "  ${CYAN}→${NC} PID File: ${PID_FILE}"
    echo "  ${CYAN}→${NC} Log File: ${LOG_FILE}"
    echo ""

    echo "${BOLD}Service Status:${NC} $(get_status)"
    echo "${BOLD}Weaviate Status:${NC} $(get_weaviate_status)"
    echo ""

    if is_running; then
        show_access_urls
    fi

    read -p "Press Enter to continue..."
}

# 查看日志
view_logs() {
    print_header
    echo "${BOLD}View Logs${NC}"
    print_separator
    echo ""

    if [ ! -f "$LOG_FILE" ]; then
        print_warning "Log file not found: $LOG_FILE"
        echo ""
        read -p "Press Enter to continue..."
        return
    fi

    echo "Log options:"
    echo "  ${GREEN}1)${NC} View last 50 lines"
    echo "  ${GREEN}2)${NC} View last 100 lines"
    echo "  ${GREEN}3)${NC} View last 500 lines"
    echo "  ${GREEN}4)${NC} Follow logs (tail -f)"
    echo "  ${GREEN}5)${NC} View all logs (less)"
    echo ""

    read -p "Select option [${GREEN}1${NC}]: " choice

    if [ -z "$choice" ]; then
        choice=1
    fi

    echo ""
    print_separator

    case $choice in
        1)
            tail -50 "$LOG_FILE"
            ;;
        2)
            tail -100 "$LOG_FILE"
            ;;
        3)
            tail -500 "$LOG_FILE"
            ;;
        4)
            print_info "Following logs (Press Ctrl+C to exit)..."
            echo ""
            sleep 1
            tail -f "$LOG_FILE"
            ;;
        5)
            less "$LOG_FILE"
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac

    echo ""
    print_separator
    echo ""
    read -p "Press Enter to continue..."
}

# 主菜单
main_menu() {
    while true; do
        print_header

        load_config

        echo "${BOLD}Service Status:${NC} $(get_status)"
        echo "${BOLD}Weaviate Status:${NC} $(get_weaviate_status)"
        echo "${BOLD}Port:${NC} ${API_PORT}"
        echo ""

        echo "${BOLD}Main Menu${NC}"
        print_separator
        echo ""
        echo "  ${GREEN}1)${NC} Start (Background)"
        echo "  ${GREEN}2)${NC} Start (Foreground)"
        echo "  ${RED}3)${NC} Stop"
        echo "  ${YELLOW}4)${NC} Restart"
        echo ""
        echo "  ${CYAN}5)${NC} View Status"
        echo "  ${CYAN}6)${NC} View Logs"
        echo "  ${CYAN}7)${NC} Show Access URLs"
        echo ""
        echo "  ${WHITE}0)${NC} Exit"
        echo ""
        print_separator

        read -p "${CYAN}Select option: ${NC}" choice

        case $choice in
            1)
                start_background
                ;;
            2)
                start_foreground
                ;;
            3)
                stop_service
                read -p "Press Enter to continue..."
                ;;
            4)
                restart_service
                ;;
            5)
                show_status
                ;;
            6)
                view_logs
                ;;
            7)
                load_config
                show_access_urls
                read -p "Press Enter to continue..."
                ;;
            0)
                echo ""
                print_success "Goodbye!"
                echo ""
                exit 0
                ;;
            *)
                print_error "Invalid option"
                sleep 1
                ;;
        esac
    done
}

# ============================================================
# 入口点
# ============================================================

# 检查是否为命令行模式
if [ $# -gt 0 ]; then
    # 命令行模式
    load_config

    case "$1" in
        start)
            # 后台启动
            if is_running; then
                print_warning "Service is already running!"
                pid=$(cat "$PID_FILE")
                print_info "PID: ${pid}"
                exit 1
            fi

            # 启动 Weaviate
            if ! start_weaviate; then
                print_error "Cannot start service without Weaviate"
                exit 1
            fi
            echo ""

            print_info "Starting service in background..."
            nohup $PYTHON_CMD -m app.main > "$LOG_FILE" 2>&1 &
            pid=$!
            echo $pid > "$PID_FILE"
            sleep 2

            if ps -p "$pid" > /dev/null 2>&1; then
                print_success "Service started (PID: ${pid})"
                show_access_urls
            else
                print_error "Failed to start service"
                rm -f "$PID_FILE"
                exit 1
            fi
            ;;

        fg|foreground)
            # 前台启动
            if is_running; then
                print_warning "Service is already running in background"
                print_info "Stop it first: ./start.sh stop"
                exit 1
            fi

            # 启动 Weaviate
            if ! start_weaviate; then
                print_error "Cannot start service without Weaviate"
                exit 1
            fi
            echo ""

            print_info "Starting service in foreground..."
            show_access_urls
            echo ""
            print_separator
            echo ""
            $PYTHON_CMD -m app.main
            ;;

        stop)
            stop_service
            ;;

        restart)
            stop_service
            sleep 1

            # 启动 Weaviate
            if ! start_weaviate; then
                print_error "Cannot start service without Weaviate"
                exit 1
            fi
            echo ""

            print_info "Starting service..."
            nohup $PYTHON_CMD -m app.main > "$LOG_FILE" 2>&1 &
            pid=$!
            echo $pid > "$PID_FILE"
            sleep 2

            if ps -p "$pid" > /dev/null 2>&1; then
                print_success "Service restarted (PID: ${pid})"
                show_access_urls
            else
                print_error "Failed to restart service"
                rm -f "$PID_FILE"
                exit 1
            fi
            ;;

        status)
            echo "Service Status: $(get_status)"
            echo "Weaviate Status: $(get_weaviate_status)"
            if is_running; then
                show_access_urls
            fi
            ;;

        logs)
            if [ ! -f "$LOG_FILE" ]; then
                print_error "Log file not found: $LOG_FILE"
                exit 1
            fi
            tail -f "$LOG_FILE"
            ;;

        urls)
            show_access_urls
            ;;

        *)
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  start         - Start service in background"
            echo "  fg|foreground - Start service in foreground"
            echo "  stop          - Stop service"
            echo "  restart       - Restart service"
            echo "  status        - Show service status"
            echo "  logs          - View logs (follow mode)"
            echo "  urls          - Show access URLs"
            echo ""
            echo "Examples:"
            echo "  $0 start       # Start in background"
            echo "  $0 fg          # Start in foreground"
            echo "  $0 stop        # Stop service"
            echo "  $0 restart     # Restart service"
            echo "  $0 logs        # View logs"
            echo "  $0 urls        # Show URLs"
            echo ""
            echo "Or run without arguments for interactive mode:"
            echo "  $0"
            echo ""
            exit 1
            ;;
    esac
else
    # 交互式模式
    main_menu
fi
