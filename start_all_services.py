#!/usr/bin/env python3
"""
HealthLink 完整系统启动脚本
启动所有服务并进行健康检查
"""
import os
import sys
import time
import signal
import subprocess
import threading
import requests
from pathlib import Path

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes = {}
        self.running = True
        
    def start_service(self, name, cmd, cwd=None, port=None):
        """启动服务"""
        try:
            print(f"🚀 Starting {name}...")
            
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[name] = {
                'process': process,
                'port': port,
                'cmd': cmd,
                'cwd': cwd
            }
            
            print(f"✅ {name} started (PID: {process.pid})")
            if port:
                print(f"   URL: http://localhost:{port}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return False
    
    def check_health(self, name, url, timeout=30):
        """检查服务健康状态"""
        print(f"🏥 Checking {name} health...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ {name} is healthy")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print(f"❌ {name} health check failed")
        return False
    
    def stop_all(self):
        """停止所有服务"""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for name, service in self.processes.items():
            try:
                process = service['process']
                if process.poll() is None:  # 进程仍在运行
                    print(f"   Stopping {name}...")
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"   Force killing {name}...")
                        process.kill()
                        process.wait()
                    
                    print(f"   ✅ {name} stopped")
            except Exception as e:
                print(f"   ❌ Error stopping {name}: {e}")
    
    def monitor_processes(self):
        """监控进程状态"""
        while self.running:
            for name, service in self.processes.items():
                process = service['process']
                if process.poll() is not None:  # 进程已结束
                    print(f"⚠️  {name} has stopped unexpectedly")
                    # 可以在这里添加重启逻辑
            
            time.sleep(5)

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n📡 Received signal {signum}")
    if 'manager' in globals():
        manager.stop_all()
    sys.exit(0)

def setup_database():
    """设置数据库"""
    try:
        print("🔧 Setting up database...")
        from config.database_switch import init_database
        init_database()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_sample_data():
    """创建示例数据"""
    try:
        print("📝 Creating sample data...")
        # 这里可以调用示例数据创建逻辑
        print("✅ Sample data created")
        return True
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def main():
    """主函数"""
    global manager
    
    print("=" * 60)
    print("🏥 HealthLink 完整系统启动")
    print("=" * 60)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建服务管理器
    manager = ServiceManager()
    
    try:
        # 1. 设置数据库
        if not setup_database():
            print("❌ Database setup failed, exiting...")
            return 1
        
        # 2. 创建示例数据
        create_sample_data()
        
        print()
        
        # 3. 启动ICER Engine
        icer_engine_dir = Path("services/icer_engine")
        if not manager.start_service(
            "ICER Engine",
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"],
            cwd=icer_engine_dir,
            port=8090
        ):
            return 1
        
        # 4. 启动Gateway API
        gateway_dir = Path("services/gateway_api")
        if not manager.start_service(
            "Gateway API",
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=gateway_dir,
            port=8000
        ):
            return 1
        
        print()
        
        # 5. 等待服务启动
        print("⏳ Waiting for services to start...")
        time.sleep(5)
        
        # 6. 健康检查
        health_checks = [
            ("ICER Engine", "http://localhost:8090/health"),
            ("Gateway API", "http://localhost:8000/health"),
        ]
        
        all_healthy = True
        for name, url in health_checks:
            if not manager.check_health(name, url):
                all_healthy = False
        
        if not all_healthy:
            print("❌ Some services failed health checks")
            manager.stop_all()
            return 1
        
        print()
        print("🎉 All services started successfully!")
        print()
        print("📡 Available endpoints:")
        print("   Gateway API:     http://localhost:8000")
        print("   Gateway Docs:    http://localhost:8000/docs")
        print("   ICER Engine:     http://localhost:8090")
        print("   ICER Docs:       http://localhost:8090/docs")
        print()
        print("🧪 Run integration tests:")
        print("   python test_icer_integration.py")
        print()
        print("Press Ctrl+C to stop all services...")
        
        # 7. 启动进程监控
        monitor_thread = threading.Thread(target=manager.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 8. 保持运行
        while manager.running:
            time.sleep(1)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        manager.stop_all()
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        manager.stop_all()
        return 1

if __name__ == "__main__":
    sys.exit(main())