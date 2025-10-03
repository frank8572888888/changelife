#!/usr/bin/env python3
"""
智能目标检测系统 - 主程序入口
"""
import os
import sys
import argparse
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.cli import GoalTrackerCLI
from src.database.database import DatabaseManager
from src.models.prediction_engine import PredictionEngine


def setup_environment():
    """设置环境"""
    # 创建必要的目录
    directories = ['data', 'models', 'logs', 'charts', 'reports']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # 检查环境变量
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_key:
        print("⚠️ 未设置DEEPSEEK_API_KEY环境变量，AI功能将不可用")
        print("   如需使用AI功能，请设置环境变量：")
        print("   export DEEPSEEK_API_KEY='your_api_key'")
        print()


def run_cli():
    """运行命令行界面"""
    try:
        cli = GoalTrackerCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
        sys.exit(1)


def run_demo():
    """运行演示模式"""
    print("🎯 智能目标检测系统 - 演示模式")
    print("=" * 50)
    
    try:
        # 初始化系统
        db = DatabaseManager()
        engine = PredictionEngine(db)
        
        print("✅ 系统初始化成功")
        
        # 显示系统状态
        summary = db.get_data_summary()
        print(f"\n📊 当前数据状态:")
        print(f"   • 活跃目标: {summary['active_goals']}个")
        print(f"   • 状态记录: {summary['state_records']}条")
        print(f"   • 活动记录: {summary['activity_records']}条")
        print(f"   • 预测记录: {summary['prediction_records']}条")
        
        if summary['active_goals'] == 0:
            print("\n💡 建议:")
            print("   1. 运行 'python main.py' 启动完整界面")
            print("   2. 创建第一个目标")
            print("   3. 开始记录每日状态和活动")
            print("   4. 获得智能预测和建议")
        else:
            print("\n🎉 系统运行正常，数据充足！")
            print("   运行 'python main.py' 查看详细分析")
        
    except Exception as e:
        print(f"❌ 演示模式运行错误: {e}")


def run_test():
    """运行测试模式"""
    print("🧪 智能目标检测系统 - 测试模式")
    print("=" * 50)
    
    try:
        # 测试数据库连接
        print("🔍 测试数据库连接...")
        db = DatabaseManager()
        summary = db.get_data_summary()
        print("✅ 数据库连接正常")
        
        # 测试预测引擎
        print("🔍 测试预测引擎...")
        engine = PredictionEngine(db)
        print("✅ 预测引擎初始化正常")
        
        # 测试ML模型
        print("🔍 测试ML模型...")
        if engine.ml_predictor.is_model_available():
            print("✅ ML模型可用")
        else:
            print("⚠️ ML模型不可用（需要更多训练数据）")
        
        # 测试AI客户端
        print("🔍 测试AI客户端...")
        if engine.ai_predictor and engine.ai_predictor.ai_client.is_available():
            print("✅ AI客户端可用")
        else:
            print("⚠️ AI客户端不可用（需要设置API密钥）")
        
        print("\n🎉 系统测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能目标检测系统 - 个人生产力管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py              # 启动完整的命令行界面
  python main.py --demo       # 运行演示模式
  python main.py --test       # 运行测试模式
  
环境变量:
  DEEPSEEK_API_KEY            # DeepSeek API密钥（可选，用于AI功能）
  
更多信息请查看 README.md
        """
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='运行演示模式，显示系统状态'
    )
    
    parser.add_argument(
        '--test',
        action='store_true', 
        help='运行测试模式，检查系统组件'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='智能目标检测系统 v1.0.0'
    )
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 根据参数选择运行模式
    if args.demo:
        run_demo()
    elif args.test:
        run_test()
    else:
        run_cli()


if __name__ == "__main__":
    main()