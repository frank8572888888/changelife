#!/usr/bin/env python3
"""
创建演示数据
"""
import sys
import os
from datetime import datetime, date, timedelta
import random

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.database import DatabaseManager
from src.database.models import Goal, DailyState, DailyActivity, GoalCategory, ActivityType


def create_demo_data():
    """创建演示数据"""
    print("🎯 创建演示数据...")
    
    db = DatabaseManager()
    
    # 创建示例目标
    goals_data = [
        {
            "name": "学习Python编程",
            "category": GoalCategory.LEARNING,
            "description": "完成Python基础教程，掌握核心概念",
            "target_value": 100.0,
            "current_value": 35.0,
            "unit": "页",
            "priority": 5,
            "deadline": datetime.now() + timedelta(days=45)
        },
        {
            "name": "每日运动健身",
            "category": GoalCategory.FITNESS,
            "description": "保持每日30分钟运动习惯",
            "target_value": 30.0,
            "current_value": 18.0,
            "unit": "天",
            "priority": 4,
            "deadline": datetime.now() + timedelta(days=30)
        },
        {
            "name": "完成项目报告",
            "category": GoalCategory.WORK,
            "description": "完成Q4季度项目总结报告",
            "target_value": 1.0,
            "current_value": 0.6,
            "unit": "份",
            "priority": 5,
            "deadline": datetime.now() + timedelta(days=14)
        }
    ]
    
    created_goals = []
    for goal_data in goals_data:
        goal = Goal(**goal_data)
        goal_id = db.create_goal(goal)
        goal.id = goal_id
        created_goals.append(goal)
        print(f"✅ 创建目标: {goal.name}")
    
    # 创建最近30天的状态记录
    print("\n📊 创建状态记录...")
    for i in range(30):
        record_date = date.today() - timedelta(days=i)
        
        # 模拟真实的状态变化
        base_mood = 6 + random.gauss(0, 1.5)
        base_energy = 6 + random.gauss(0, 1.2)
        base_stress = 5 + random.gauss(0, 1.0)
        
        # 周末通常心情更好，压力更小
        if record_date.weekday() >= 5:
            base_mood += 1
            base_stress -= 1
        
        # 工作日精力可能更高
        if record_date.weekday() < 5:
            base_energy += 0.5
        
        state = DailyState(
            date=datetime.combine(record_date, datetime.min.time()),
            mood=max(1, min(10, int(base_mood))),
            energy=max(1, min(10, int(base_energy))),
            stress=max(1, min(10, int(base_stress))),
            sleep_hours=7.0 + random.gauss(0, 1.0),
            sleep_quality=max(1, min(10, int(6 + random.gauss(0, 1.5)))),
            focus=max(1, min(10, int(6 + random.gauss(0, 1.2)))),
            motivation=max(1, min(10, int(6 + random.gauss(0, 1.3)))),
            health=max(1, min(10, int(7 + random.gauss(0, 1.0)))),
            notes=f"第{31-i}天记录" if i % 7 == 0 else ""
        )
        
        db.save_daily_state(state)
    
    print(f"✅ 创建了30天的状态记录")
    
    # 创建活动记录
    print("\n📝 创建活动记录...")
    activity_count = 0
    
    for i in range(25):  # 最近25天有活动记录
        record_date = date.today() - timedelta(days=i)
        
        # 每天1-3个活动
        daily_activities = random.randint(1, 3)
        
        for j in range(daily_activities):
            # 随机选择目标和活动类型
            goal = random.choice(created_goals)
            
            if goal.category == GoalCategory.LEARNING:
                activity_type = ActivityType.STUDY
                duration = random.randint(30, 120)
                description = f"学习{goal.name.split('学习')[1]}"
            elif goal.category == GoalCategory.FITNESS:
                activity_type = ActivityType.EXERCISE
                duration = random.randint(20, 60)
                description = "跑步/健身训练"
            else:
                activity_type = ActivityType.WORK
                duration = random.randint(60, 180)
                description = f"处理{goal.name}"
            
            # 模拟效率和进度的相关性
            base_efficiency = 6 + random.gauss(0, 1.5)
            efficiency = max(1, min(10, int(base_efficiency)))
            
            # 进度与效率相关
            progress = max(0, min(100, efficiency * 10 + random.gauss(0, 15)))
            
            activity = DailyActivity(
                date=datetime.combine(record_date, datetime.min.time()),
                activity_type=activity_type,
                description=description,
                duration_minutes=duration,
                efficiency=efficiency,
                progress=progress,
                goal_id=goal.id,
                satisfaction=max(1, min(10, int(efficiency + random.gauss(0, 1)))),
                notes=f"活动记录{activity_count + 1}" if activity_count % 10 == 0 else ""
            )
            
            db.save_daily_activity(activity)
            activity_count += 1
    
    print(f"✅ 创建了{activity_count}条活动记录")
    
    print("\n🎉 演示数据创建完成！")
    print("\n📊 数据概览:")
    summary = db.get_data_summary()
    print(f"   • 活跃目标: {summary['active_goals']}个")
    print(f"   • 状态记录: {summary['state_records']}条")
    print(f"   • 活动记录: {summary['activity_records']}条")
    
    print("\n💡 现在您可以:")
    print("   1. 运行 'python main.py' 体验完整功能")
    print("   2. 查看目标管理和预测分析")
    print("   3. 尝试训练机器学习模型")


if __name__ == "__main__":
    create_demo_data()