#!/usr/bin/env python3
"""
HealthLink 质量检查脚本
运行所有质量门禁检查
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, cwd=None, timeout=60):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_python_quality():
    """检查Python代码质量"""
    print("🔍 Checking Python code quality...")
    
    checks = [
        ("Black formatting", "black --check ."),
        ("Import sorting", "isort --check-only ."),
        ("Ruff linting", "ruff check ."),
        ("MyPy type checking", "mypy services/icer_engine --ignore-missing-imports"),
    ]
    
    passed = 0
    for name, cmd in checks:
        success, stdout, stderr = run_command(cmd)
        if success:
            print(f"  ✅ {name}: PASSED")
            passed += 1
        else:
            print(f"  ❌ {name}: FAILED")
            if stderr:
                print(f"     Error: {stderr.strip()}")
    
    return passed, len(checks)

def check_tests():
    """运行测试"""
    print("\n🧪 Running tests...")
    
    tests = [
        ("ICER Engine unit tests", "pytest services/icer_engine/tests -v", "services/icer_engine"),
        ("Quick integration test", "python quick_test.py", "."),
    ]
    
    passed = 0
    for name, cmd, cwd in tests:
        success, stdout, stderr = run_command(cmd, cwd=cwd)
        if success:
            print(f"  ✅ {name}: PASSED")
            passed += 1
        else:
            print(f"  ❌ {name}: FAILED")
            if stderr:
                print(f"     Error: {stderr.strip()}")
    
    return passed, len(tests)

def check_openapi():
    """检查OpenAPI规范"""
    print("\n📋 Checking OpenAPI specification...")
    
    # 检查spectral是否可用
    spectral_available, _, _ = run_command("npx --version")
    
    if not spectral_available:
        print("  ⚠️  Spectral not available (npx not found), skipping OpenAPI lint")
        return 0, 1
    
    success, stdout, stderr = run_command("npx -y @stoplight/spectral-cli lint docs/openapi.yaml")
    
    if success:
        print("  ✅ OpenAPI specification: PASSED")
        return 1, 1
    else:
        print("  ❌ OpenAPI specification: FAILED")
        if stderr:
            print(f"     Error: {stderr.strip()}")
        return 0, 1

def check_docker():
    """检查Docker构建"""
    print("\n🐳 Checking Docker builds...")
    
    # 检查docker是否可用
    docker_available, _, _ = run_command("docker --version")
    
    if not docker_available:
        print("  ⚠️  Docker not available, skipping Docker checks")
        return 0, 1
    
    # 构建ICER Engine镜像
    success, stdout, stderr = run_command(
        "docker build -t icer-engine-test .", 
        cwd="services/icer_engine",
        timeout=120
    )
    
    if success:
        print("  ✅ ICER Engine Docker build: PASSED")
        # 清理测试镜像
        run_command("docker rmi icer-engine-test")
        return 1, 1
    else:
        print("  ❌ ICER Engine Docker build: FAILED")
        if stderr:
            print(f"     Error: {stderr.strip()}")
        return 0, 1

def check_service_health():
    """检查服务健康状态"""
    print("\n🏥 Checking service health...")
    
    # 检查是否有服务在运行
    services = [
        ("Gateway API", "http://localhost:8000/health"),
        ("ICER Engine", "http://localhost:8090/health"),
    ]
    
    passed = 0
    for name, url in services:
        success, stdout, stderr = run_command(f"curl -s -f {url}")
        if success:
            print(f"  ✅ {name}: RUNNING")
            passed += 1
        else:
            print(f"  ⚠️  {name}: NOT RUNNING (this is OK if not started)")
    
    return passed, len(services)

def install_dependencies():
    """安装必要的依赖"""
    print("📦 Installing quality check dependencies...")
    
    deps = [
        "black",
        "isort", 
        "ruff",
        "mypy",
        "pytest",
        "requests"
    ]
    
    for dep in deps:
        print(f"  Installing {dep}...")
        success, _, stderr = run_command(f"pip install {dep}")
        if not success:
            print(f"  ⚠️  Failed to install {dep}: {stderr}")

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 HealthLink 质量检查")
    print("=" * 60)
    
    # 安装依赖
    install_dependencies()
    print()
    
    total_passed = 0
    total_checks = 0
    
    # 运行各项检查
    checks = [
        check_python_quality,
        check_tests,
        check_openapi,
        check_docker,
        check_service_health,
    ]
    
    for check_func in checks:
        try:
            passed, total = check_func()
            total_passed += passed
            total_checks += total
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            total_checks += 1
    
    # 输出总结
    print("\n" + "=" * 60)
    print(f"📊 质量检查结果: {total_passed}/{total_checks} 通过")
    
    if total_passed == total_checks:
        print("🎉 所有质量检查通过！代码质量良好。")
        return 0
    elif total_passed >= total_checks * 0.8:
        print("⚠️  大部分检查通过，但仍有改进空间。")
        return 0
    else:
        print("❌ 多项检查失败，请修复问题后重试。")
        return 1

if __name__ == "__main__":
    sys.exit(main())