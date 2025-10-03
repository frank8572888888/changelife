#!/usr/bin/env python3
"""
模型初始化脚本
用于初始化和管理机器学习模型
"""
import os
import sys
import json
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database.database import DatabaseManager
from src.models.prediction_engine import PredictionEngine


def check_model_status():
    """检查模型状态"""
    print("🔍 检查模型状态...")
    
    model_files = [
        'success_model.joblib',
        'productivity_model.joblib',
        'encoders.joblib',
        'scaler.joblib'
    ]
    
    status = {}
    for file in model_files:
        file_path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            status[file] = {
                'exists': True,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            status[file] = {'exists': False}
    
    return status


def train_initial_models():
    """训练初始模型"""
    print("🤖 开始训练初始模型...")
    
    try:
        db = DatabaseManager()
        engine = PredictionEngine(db)
        
        # 检查数据是否足够
        summary = db.get_data_summary()
        if summary['state_records'] < 14 or summary['activity_records'] < 21:
            print("⚠️ 数据不足，无法训练模型")
            print(f"   当前状态记录: {summary['state_records']}条 (需要至少14条)")
            print(f"   当前活动记录: {summary['activity_records']}条 (需要至少21条)")
            print("   请先运行 'python demo_data.py' 创建演示数据")
            return False
        
        # 训练模型
        result = engine.train_ml_model()
        
        if result['success']:
            print("✅ 模型训练成功!")
            if 'metrics' in result:
                print(f"   成功率预测准确率: {result['metrics']['success_accuracy']:.2%}")
                print(f"   训练样本数: {result['metrics']['training_samples']}")
            return True
        else:
            print(f"❌ 模型训练失败: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ 训练过程出错: {e}")
        return False


def clean_old_models():
    """清理旧模型文件"""
    print("🧹 清理旧模型文件...")
    
    model_files = [
        'success_model.joblib',
        'productivity_model.joblib',
        'encoders.joblib',
        'scaler.joblib'
    ]
    
    cleaned = 0
    for file in model_files:
        file_path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(file_path):
            os.remove(file_path)
            cleaned += 1
            print(f"   删除: {file}")
    
    print(f"✅ 清理完成，删除了{cleaned}个文件")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="模型管理工具")
    parser.add_argument('--status', action='store_true', help='检查模型状态')
    parser.add_argument('--train', action='store_true', help='训练新模型')
    parser.add_argument('--clean', action='store_true', help='清理旧模型')
    
    args = parser.parse_args()
    
    if args.status:
        status = check_model_status()
        print("\n📊 模型状态:")
        for file, info in status.items():
            if info['exists']:
                print(f"   ✅ {file}: {info['size']} bytes, 修改时间: {info['modified']}")
            else:
                print(f"   ❌ {file}: 不存在")
    
    elif args.train:
        train_initial_models()
    
    elif args.clean:
        clean_old_models()
    
    else:
        print("🤖 模型管理工具")
        print("使用方法:")
        print("  python init_models.py --status   # 检查模型状态")
        print("  python init_models.py --train    # 训练新模型")
        print("  python init_models.py --clean    # 清理旧模型")


if __name__ == "__main__":
    main()