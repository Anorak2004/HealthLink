#!/usr/bin/env python3
"""
ICER Engine 启动脚本
独立启动ICER评估服务
"""
import os
import sys
import subprocess
from pathlib import Path

def start_icer_engine():
    """启动ICER Engine服务"""
    try:
        # 切换到ICER Engine目录
        icer_dir = Path(__file__).parent / "services" / "icer_engine"
        
        if not icer_dir.exists():
            print(f"❌ ICER Engine directory not found: {icer_dir}")
            return False
        
        print("🚀 Starting ICER Engine...")
        print(f"📁 Working directory: {icer_dir}")
        print("📡 Service will be available at: http://localhost:8090")
        print("📚 API documentation: http://localhost:8090/docs")
        print("🏥 Health check: http://localhost:8090/health")
        print()
        
        # 检查requirements.txt是否存在
        requirements_file = icer_dir / "requirements.txt"
        if requirements_file.exists():
            print("📦 Installing dependencies...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], cwd=icer_dir, check=True)
            print("✅ Dependencies installed")
        
        # 启动服务
        print("🔄 Starting uvicorn server...")
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8090",
            "--reload"
        ], cwd=icer_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start ICER Engine: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 ICER Engine stopped by user")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🏥 ICER Engine - 成本效果比评估服务")
    print("=" * 50)
    print()
    
    success = start_icer_engine()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())