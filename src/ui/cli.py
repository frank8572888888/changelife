"""
命令行界面
提供友好的命令行交互界面
"""
import os
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.database import DatabaseManager
from src.database.models import Goal, DailyState, DailyActivity, GoalCategory, ActivityType
from src.models.prediction_engine import PredictionEngine


class GoalTrackerCLI:
    """目标追踪命令行界面"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.prediction_engine = PredictionEngine(self.db, os.getenv("DEEPSEEK_API_KEY"))
        self.current_user = "用户"  # 可以扩展为多用户系统
        
    def run(self):
        """运行主程序"""
        self.show_welcome()
        
        while True:
            try:
                self.show_main_menu()
                choice = input("\n请选择操作 (输入数字): ").strip()
                
                if choice == '1':
                    self.manage_goals()
                elif choice == '2':
                    self.record_daily_state()
                elif choice == '3':
                    self.record_daily_activity()
                elif choice == '4':
                    self.predict_goals()
                elif choice == '5':
                    self.view_insights()
                elif choice == '6':
                    self.train_model()
                elif choice == '7':
                    self.view_data_summary()
                elif choice == '8':
                    self.export_data()
                elif choice == '0' or choice.lower() == 'q':
                    self.show_goodbye()
                    break
                else:
                    print("❌ 无效选择，请重新输入")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                input("按回车键继续...")
    
    def show_welcome(self):
        """显示欢迎信息"""
        print("=" * 60)
        print("🎯 智能目标检测系统")
        print("=" * 60)
        print("欢迎使用个人目标管理和预测系统！")
        print("本系统将帮助您:")
        print("• 设定和管理个人目标")
        print("• 记录每日状态和活动")
        print("• 预测目标达成概率")
        print("• 获得个性化改进建议")
        print("=" * 60)
    
    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 40)
        print("📋 主菜单")
        print("=" * 40)
        print("1. 🎯 目标管理")
        print("2. 😊 记录今日状态")
        print("3. 📝 记录今日活动")
        print("4. 🔮 预测分析")
        print("5. 💡 洞察报告")
        print("6. 🤖 训练模型")
        print("7. 📊 数据概览")
        print("8. 💾 导出数据")
        print("0. 👋 退出系统")
        print("=" * 40)
    
    def manage_goals(self):
        """目标管理"""
        while True:
            print("\n" + "=" * 30)
            print("🎯 目标管理")
            print("=" * 30)
            print("1. 查看所有目标")
            print("2. 创建新目标")
            print("3. 更新目标进度")
            print("4. 编辑目标")
            print("5. 删除目标")
            print("0. 返回主菜单")
            
            choice = input("\n请选择操作: ").strip()
            
            if choice == '1':
                self.view_goals()
            elif choice == '2':
                self.create_goal()
            elif choice == '3':
                self.update_goal_progress()
            elif choice == '4':
                self.edit_goal()
            elif choice == '5':
                self.delete_goal()
            elif choice == '0':
                break
            else:
                print("❌ 无效选择")
    
    def view_goals(self):
        """查看所有目标"""
        goals = self.db.get_active_goals()
        
        if not goals:
            print("\n📝 暂无活跃目标，建议创建第一个目标！")
            return
        
        print(f"\n📋 您的活跃目标 (共{len(goals)}个):")
        print("-" * 80)
        
        for i, goal in enumerate(goals, 1):
            completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
            progress_bar = self.create_progress_bar(completion_rate)
            
            print(f"{i}. {goal.name}")
            print(f"   类别: {goal.category.value} | 优先级: {goal.priority}/5")
            print(f"   进度: {goal.current_value}/{goal.target_value} {goal.unit} {progress_bar}")
            
            if goal.deadline:
                days_left = (goal.deadline - datetime.now()).days
                if days_left > 0:
                    print(f"   截止: {goal.deadline.strftime('%Y-%m-%d')} (还有{days_left}天)")
                else:
                    print(f"   截止: {goal.deadline.strftime('%Y-%m-%d')} (已过期{abs(days_left)}天)")
            
            if goal.description:
                print(f"   描述: {goal.description}")
            
            print("-" * 80)
    
    def create_goal(self):
        """创建新目标"""
        print("\n✨ 创建新目标")
        print("-" * 30)
        
        try:
            # 基本信息
            name = input("目标名称: ").strip()
            if not name:
                print("❌ 目标名称不能为空")
                return
            
            description = input("目标描述 (可选): ").strip()
            
            # 选择类别
            print("\n目标类别:")
            categories = list(GoalCategory)
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat.value}")
            
            cat_choice = input("选择类别 (输入数字): ").strip()
            try:
                category = categories[int(cat_choice) - 1]
            except (ValueError, IndexError):
                category = GoalCategory.PERSONAL
                print(f"使用默认类别: {category.value}")
            
            # 目标值和单位
            target_value = self.get_float_input("目标值 (如: 100): ", 1.0)
            unit = input("单位 (如: 页, 公里, 小时): ").strip()
            
            # 优先级
            priority = self.get_int_input("优先级 (1-5, 5最高): ", 3, 1, 5)
            
            # 截止日期
            deadline_str = input("截止日期 (YYYY-MM-DD, 可选): ").strip()
            deadline = None
            if deadline_str:
                try:
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                except ValueError:
                    print("⚠️ 日期格式错误，将不设置截止日期")
            
            # 创建目标
            goal = Goal(
                name=name,
                description=description,
                category=category,
                target_value=target_value,
                unit=unit,
                priority=priority,
                deadline=deadline
            )
            
            goal_id = self.db.create_goal(goal)
            print(f"✅ 目标创建成功！ID: {goal_id}")
            
        except Exception as e:
            print(f"❌ 创建目标失败: {e}")
    
    def update_goal_progress(self):
        """更新目标进度"""
        goals = self.db.get_active_goals()
        
        if not goals:
            print("\n📝 暂无活跃目标")
            return
        
        print("\n📈 更新目标进度")
        print("-" * 30)
        
        # 显示目标列表
        for i, goal in enumerate(goals, 1):
            completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
            print(f"{i}. {goal.name} - 当前: {goal.current_value}/{goal.target_value} {goal.unit} ({completion_rate:.1%})")
        
        try:
            choice = self.get_int_input("\n选择要更新的目标 (输入数字): ", 1, 1, len(goals))
            goal = goals[choice - 1]
            
            print(f"\n更新目标: {goal.name}")
            print(f"当前进度: {goal.current_value}/{goal.target_value} {goal.unit}")
            
            new_value = self.get_float_input(f"新的当前值: ", goal.current_value)
            goal.current_value = new_value
            
            if self.db.update_goal(goal):
                completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
                print(f"✅ 进度更新成功！当前完成度: {completion_rate:.1%}")
                
                if completion_rate >= 1.0:
                    print("🎉 恭喜！目标已完成！")
            else:
                print("❌ 更新失败")
                
        except Exception as e:
            print(f"❌ 更新失败: {e}")
    
    def edit_goal(self):
        """编辑目标"""
        goals = self.db.get_active_goals()
        
        if not goals:
            print("\n📝 暂无活跃目标")
            return
        
        print("\n✏️ 编辑目标")
        print("-" * 30)
        
        # 显示目标列表
        for i, goal in enumerate(goals, 1):
            print(f"{i}. {goal.name}")
        
        try:
            choice = self.get_int_input("\n选择要编辑的目标 (输入数字): ", 1, 1, len(goals))
            goal = goals[choice - 1]
            
            print(f"\n编辑目标: {goal.name}")
            print("(直接回车保持原值)")
            
            # 编辑各个字段
            new_name = input(f"名称 [{goal.name}]: ").strip()
            if new_name:
                goal.name = new_name
            
            new_desc = input(f"描述 [{goal.description}]: ").strip()
            if new_desc:
                goal.description = new_desc
            
            new_target = input(f"目标值 [{goal.target_value}]: ").strip()
            if new_target:
                try:
                    goal.target_value = float(new_target)
                except ValueError:
                    print("⚠️ 目标值格式错误，保持原值")
            
            new_unit = input(f"单位 [{goal.unit}]: ").strip()
            if new_unit:
                goal.unit = new_unit
            
            new_priority = input(f"优先级 (1-5) [{goal.priority}]: ").strip()
            if new_priority:
                try:
                    priority = int(new_priority)
                    if 1 <= priority <= 5:
                        goal.priority = priority
                    else:
                        print("⚠️ 优先级必须在1-5之间，保持原值")
                except ValueError:
                    print("⚠️ 优先级格式错误，保持原值")
            
            if self.db.update_goal(goal):
                print("✅ 目标更新成功！")
            else:
                print("❌ 更新失败")
                
        except Exception as e:
            print(f"❌ 编辑失败: {e}")
    
    def delete_goal(self):
        """删除目标"""
        goals = self.db.get_active_goals()
        
        if not goals:
            print("\n📝 暂无活跃目标")
            return
        
        print("\n🗑️ 删除目标")
        print("-" * 30)
        
        # 显示目标列表
        for i, goal in enumerate(goals, 1):
            print(f"{i}. {goal.name}")
        
        try:
            choice = self.get_int_input("\n选择要删除的目标 (输入数字): ", 1, 1, len(goals))
            goal = goals[choice - 1]
            
            confirm = input(f"\n确认删除目标 '{goal.name}'? (y/N): ").strip().lower()
            
            if confirm == 'y':
                if self.db.delete_goal(goal.id):
                    print("✅ 目标删除成功！")
                else:
                    print("❌ 删除失败")
            else:
                print("❌ 取消删除")
                
        except Exception as e:
            print(f"❌ 删除失败: {e}")
    
    def record_daily_state(self):
        """记录每日状态"""
        print("\n😊 记录今日状态")
        print("-" * 30)
        print("请为以下各项打分 (1-10分，10分最好):")
        
        try:
            today = date.today()
            existing_state = self.db.get_daily_state(today)
            
            if existing_state:
                print(f"⚠️ 今日({today})已有状态记录，将更新现有记录")
                state = existing_state
            else:
                state = DailyState(date=datetime.now())
            
            # 记录各项状态
            state.mood = self.get_int_input(f"心情状态 [{getattr(state, 'mood', 5)}]: ", getattr(state, 'mood', 5), 1, 10)
            state.energy = self.get_int_input(f"精力水平 [{getattr(state, 'energy', 5)}]: ", getattr(state, 'energy', 5), 1, 10)
            state.stress = self.get_int_input(f"压力水平 [{getattr(state, 'stress', 5)}]: ", getattr(state, 'stress', 5), 1, 10)
            state.sleep_hours = self.get_float_input(f"睡眠时长 [{getattr(state, 'sleep_hours', 8.0)}]: ", getattr(state, 'sleep_hours', 8.0))
            state.sleep_quality = self.get_int_input(f"睡眠质量 [{getattr(state, 'sleep_quality', 5)}]: ", getattr(state, 'sleep_quality', 5), 1, 10)
            state.focus = self.get_int_input(f"专注度 [{getattr(state, 'focus', 5)}]: ", getattr(state, 'focus', 5), 1, 10)
            state.motivation = self.get_int_input(f"动机水平 [{getattr(state, 'motivation', 5)}]: ", getattr(state, 'motivation', 5), 1, 10)
            state.health = self.get_int_input(f"健康状况 [{getattr(state, 'health', 5)}]: ", getattr(state, 'health', 5), 1, 10)
            
            notes = input("备注 (可选): ").strip()
            if notes:
                state.notes = notes
            
            # 保存状态
            state_id = self.db.save_daily_state(state)
            print(f"✅ 今日状态记录成功！ID: {state_id}")
            
            # 显示状态摘要
            self.show_state_summary(state)
            
        except Exception as e:
            print(f"❌ 记录状态失败: {e}")
    
    def record_daily_activity(self):
        """记录每日活动"""
        print("\n📝 记录今日活动")
        print("-" * 30)
        
        try:
            activity = DailyActivity(date=datetime.now())
            
            # 选择活动类型
            print("\n活动类型:")
            activity_types = list(ActivityType)
            for i, atype in enumerate(activity_types, 1):
                print(f"{i}. {atype.value}")
            
            type_choice = input("选择活动类型 (输入数字): ").strip()
            try:
                activity.activity_type = activity_types[int(type_choice) - 1]
            except (ValueError, IndexError):
                activity.activity_type = ActivityType.WORK
                print(f"使用默认类型: {activity.activity_type.value}")
            
            # 活动描述
            activity.description = input("活动描述: ").strip()
            if not activity.description:
                activity.description = f"{activity.activity_type.value}活动"
            
            # 持续时间
            activity.duration_minutes = self.get_int_input("持续时间 (分钟): ", 60, 1)
            
            # 效率评分
            activity.efficiency = self.get_int_input("执行效率 (1-10): ", 5, 1, 10)
            
            # 完成进度
            activity.progress = self.get_float_input("完成进度 (0-100%): ", 50.0, 0, 100)
            
            # 满意度
            activity.satisfaction = self.get_int_input("满意度 (1-10): ", 5, 1, 10)
            
            # 关联目标
            goals = self.db.get_active_goals()
            if goals:
                print("\n关联目标 (可选):")
                print("0. 不关联目标")
                for i, goal in enumerate(goals, 1):
                    print(f"{i}. {goal.name}")
                
                goal_choice = input("选择关联目标 (输入数字): ").strip()
                try:
                    choice_num = int(goal_choice)
                    if 1 <= choice_num <= len(goals):
                        activity.goal_id = goals[choice_num - 1].id
                except ValueError:
                    pass
            
            # 备注
            notes = input("备注 (可选): ").strip()
            if notes:
                activity.notes = notes
            
            # 保存活动
            activity_id = self.db.save_daily_activity(activity)
            print(f"✅ 活动记录成功！ID: {activity_id}")
            
            # 显示活动摘要
            self.show_activity_summary(activity)
            
        except Exception as e:
            print(f"❌ 记录活动失败: {e}")
    
    def predict_goals(self):
        """预测分析"""
        goals = self.db.get_active_goals()
        
        if not goals:
            print("\n📝 暂无活跃目标，请先创建目标")
            return
        
        print("\n🔮 预测分析")
        print("-" * 30)
        
        # 显示目标列表
        print("选择要预测的目标:")
        print("0. 预测所有目标")
        for i, goal in enumerate(goals, 1):
            print(f"{i}. {goal.name}")
        
        try:
            choice = self.get_int_input("\n请选择 (输入数字): ", 0, 0, len(goals))
            
            if choice == 0:
                # 预测所有目标
                for goal in goals:
                    self.predict_single_goal(goal)
                    print("-" * 50)
            else:
                # 预测单个目标
                goal = goals[choice - 1]
                self.predict_single_goal(goal, detailed=True)
                
        except Exception as e:
            print(f"❌ 预测失败: {e}")
    
    def predict_single_goal(self, goal: Goal, detailed: bool = False):
        """预测单个目标"""
        try:
            print(f"\n🎯 预测目标: {goal.name}")
            print("⏳ 正在分析...")
            
            # 执行预测
            result = self.prediction_engine.predict_goal_success(goal, include_report=detailed)
            prediction = result['prediction']
            summary = result['summary']
            
            # 显示预测结果
            print(f"✨ 预测完成！")
            print(f"📊 成功概率: {prediction['success_probability']:.1%} ({summary['success_level']})")
            print(f"⚡ 生产力评分: {prediction['productivity_score']:.1f}/10 ({summary['productivity_level']})")
            print(f"🎯 预测置信度: {prediction['confidence']:.1%} ({summary['confidence_level']})")
            print(f"🤖 预测方法: {prediction['method_used']}")
            
            # 显示关键因素
            if prediction['key_factors']:
                print(f"\n🔑 关键影响因素:")
                sorted_factors = sorted(prediction['key_factors'].items(), 
                                      key=lambda x: abs(x[1]), reverse=True)
                for factor, weight in sorted_factors[:5]:
                    impact = "积极" if weight > 0 else "消极"
                    print(f"   • {factor}: {weight:.1%} ({impact})")
            
            # 显示建议
            if prediction['recommendations']:
                print(f"\n💡 改进建议:")
                for i, rec in enumerate(prediction['recommendations'][:5], 1):
                    print(f"   {i}. {rec}")
            
            # 显示风险评估
            print(f"\n⚠️ 风险级别: {summary['risk_level']}")
            print(f"📝 关键信息: {summary['key_message']}")
            
            if detailed and result.get('detailed_report'):
                self.show_detailed_report_summary(result['detailed_report'])
                
        except Exception as e:
            print(f"❌ 预测目标 '{goal.name}' 失败: {e}")
    
    def show_detailed_report_summary(self, report: Dict[str, Any]):
        """显示详细报告摘要"""
        print(f"\n📋 详细分析报告")
        print("-" * 30)
        
        # 因素分析
        if 'factor_analysis' in report:
            factor_analysis = report['factor_analysis']
            
            if factor_analysis.get('top_positive_factors'):
                print("✅ 积极因素:")
                for factor in factor_analysis['top_positive_factors'][:3]:
                    print(f"   • {factor['factor']}: {factor['explanation']}")
            
            if factor_analysis.get('top_negative_factors'):
                print("\n❌ 需改进因素:")
                for factor in factor_analysis['top_negative_factors'][:3]:
                    print(f"   • {factor['factor']}: {factor['explanation']}")
        
        # 置信度分析
        if 'confidence_analysis' in report:
            conf_analysis = report['confidence_analysis']
            data_quality = conf_analysis.get('data_quality', {})
            
            print(f"\n📊 数据质量:")
            print(f"   • 状态记录: {data_quality.get('state_records', 0)}条")
            print(f"   • 活动记录: {data_quality.get('activity_records', 0)}条")
            print(f"   • 数据新鲜度: {data_quality.get('data_freshness', 0):.1%}")
            print(f"   • 数据完整性: {data_quality.get('data_completeness', 0):.1%}")
    
    def view_insights(self):
        """查看洞察报告"""
        print("\n💡 洞察报告")
        print("-" * 30)
        print("⏳ 正在生成洞察...")
        
        try:
            insights = self.prediction_engine.get_comprehensive_insights()
            
            if 'message' in insights:
                print(f"📝 {insights['message']}")
                return
            
            # 系统概览
            overview = insights.get('overview', {})
            print(f"📊 系统概览:")
            print(f"   • 活跃目标: {overview.get('active_goals', 0)}个")
            print(f"   • 状态记录: {overview['total_records'].get('states', 0)}条")
            print(f"   • 活动记录: {overview['total_records'].get('activities', 0)}条")
            print(f"   • 预测记录: {overview['total_records'].get('predictions', 0)}条")
            
            # 最近平均状态
            recent_avg = overview.get('recent_averages', {})
            if recent_avg:
                print(f"\n😊 最近7天平均状态:")
                print(f"   • 心情: {recent_avg.get('mood', 0):.1f}/10")
                print(f"   • 精力: {recent_avg.get('energy', 0):.1f}/10")
                print(f"   • 压力: {recent_avg.get('stress', 0):.1f}/10")
                print(f"   • 睡眠: {recent_avg.get('sleep', 0):.1f}小时")
            
            # 目标洞察
            goal_insights = insights.get('goal_insights', [])
            if goal_insights:
                print(f"\n🎯 目标洞察:")
                for insight in goal_insights[:5]:
                    goal_info = insight['goal']
                    print(f"\n   📌 {goal_info['name']} ({goal_info['category']})")
                    print(f"      完成度: {goal_info['completion_rate']:.1%}")
                    print(f"      状态: {insight['status']}")
                    
                    key_insights = insight.get('key_insights', [])
                    for ki in key_insights[:2]:
                        print(f"      • {ki}")
            
            # 全局模式
            patterns = insights.get('global_patterns', {})
            if patterns and 'message' not in patterns:
                print(f"\n🔍 行为模式:")
                if patterns.get('most_productive_weekday') != '数据不足':
                    print(f"   • 最高效日期: {patterns.get('most_productive_weekday')}")
                if patterns.get('optimal_activity_duration') != '数据不足':
                    print(f"   • 最佳持续时间: {patterns.get('optimal_activity_duration')}")
            
            # 全局建议
            recommendations = insights.get('recommendations', [])
            if recommendations:
                print(f"\n💡 系统建议:")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"   {i}. {rec}")
            
            # 数据健康度
            data_health = insights.get('data_health', {})
            if data_health:
                print(f"\n🏥 数据健康度: {data_health.get('level', '未知')} ({data_health.get('overall_score', 0)}/100)")
                
                strengths = data_health.get('strengths', [])
                if strengths:
                    print(f"   优势: {', '.join(strengths)}")
                
                weaknesses = data_health.get('weaknesses', [])
                if weaknesses:
                    print(f"   待改进: {', '.join(weaknesses)}")
            
        except Exception as e:
            print(f"❌ 生成洞察失败: {e}")
    
    def train_model(self):
        """训练模型"""
        print("\n🤖 训练机器学习模型")
        print("-" * 30)
        print("⏳ 正在训练模型，请稍候...")
        
        try:
            result = self.prediction_engine.train_ml_model()
            
            if result['success']:
                print("✅ 模型训练成功！")
                
                if 'metrics' in result:
                    metrics = result['metrics']
                    print(f"\n📊 模型性能:")
                    print(f"   • 准确率: {metrics.get('success_accuracy', 0):.1%}")
                    print(f"   • 精确率: {metrics.get('success_precision', 0):.1%}")
                    print(f"   • 召回率: {metrics.get('success_recall', 0):.1%}")
                    print(f"   • F1分数: {metrics.get('success_f1', 0):.1%}")
                    print(f"   • 训练样本: {metrics.get('training_samples', 0)}个")
                    
                    if metrics.get('success_accuracy', 0) > 0.8:
                        print("🎉 模型性能优秀！")
                    elif metrics.get('success_accuracy', 0) > 0.6:
                        print("👍 模型性能良好")
                    else:
                        print("⚠️ 模型性能一般，建议增加更多数据")
                
                print(f"\n💡 {result['message']}")
            else:
                print(f"❌ 模型训练失败: {result['message']}")
                
                if "数据不足" in result['message']:
                    print("\n📝 建议:")
                    print("   • 继续记录每日状态和活动")
                    print("   • 至少需要30个训练样本")
                    print("   • 保持记录的一致性")
                
        except Exception as e:
            print(f"❌ 训练模型失败: {e}")
    
    def view_data_summary(self):
        """查看数据概览"""
        print("\n📊 数据概览")
        print("-" * 30)
        
        try:
            summary = self.db.get_data_summary()
            
            print(f"🎯 目标统计:")
            print(f"   • 活跃目标: {summary['active_goals']}个")
            
            print(f"\n📝 记录统计:")
            print(f"   • 状态记录: {summary['state_records']}条")
            print(f"   • 活动记录: {summary['activity_records']}条")
            print(f"   • 预测记录: {summary['prediction_records']}条")
            
            recent_avg = summary['recent_averages']
            if any(v > 0 for v in recent_avg.values()):
                print(f"\n😊 最近7天平均状态:")
                print(f"   • 心情: {recent_avg['mood']:.1f}/10")
                print(f"   • 精力: {recent_avg['energy']:.1f}/10")
                print(f"   • 压力: {recent_avg['stress']:.1f}/10")
                print(f"   • 睡眠: {recent_avg['sleep']:.1f}小时")
            
            # 数据质量评估
            total_records = summary['state_records'] + summary['activity_records']
            if total_records >= 50:
                quality = "优秀"
            elif total_records >= 20:
                quality = "良好"
            elif total_records >= 10:
                quality = "一般"
            else:
                quality = "需改进"
            
            print(f"\n🏥 数据质量: {quality}")
            
            if quality == "需改进":
                print("\n💡 建议:")
                print("   • 每日记录状态和活动")
                print("   • 保持记录的一致性")
                print("   • 至少记录2周以上获得更好的预测效果")
            
        except Exception as e:
            print(f"❌ 获取数据概览失败: {e}")
    
    def export_data(self):
        """导出数据"""
        print("\n💾 导出数据")
        print("-" * 30)
        
        try:
            # 获取所有数据
            goals = self.db.get_active_goals()
            states = self.db.get_recent_states(365)  # 最近一年
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "goals": [],
                "states": [],
                "summary": self.db.get_data_summary()
            }
            
            # 导出目标
            for goal in goals:
                goal_data = {
                    "id": goal.id,
                    "name": goal.name,
                    "category": goal.category.value,
                    "description": goal.description,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                    "unit": goal.unit,
                    "priority": goal.priority,
                    "deadline": goal.deadline.isoformat() if goal.deadline else None,
                    "created_at": goal.created_at.isoformat() if goal.created_at else None
                }
                
                # 添加目标的活动记录
                activities = self.db.get_goal_activities(goal.id, 365)
                goal_data["activities"] = []
                
                for activity in activities:
                    activity_data = {
                        "date": activity.date.isoformat() if activity.date else None,
                        "type": activity.activity_type.value,
                        "description": activity.description,
                        "duration_minutes": activity.duration_minutes,
                        "efficiency": activity.efficiency,
                        "progress": activity.progress,
                        "satisfaction": activity.satisfaction
                    }
                    goal_data["activities"].append(activity_data)
                
                export_data["goals"].append(goal_data)
            
            # 导出状态
            for state in states:
                state_data = {
                    "date": state.date.isoformat(),
                    "mood": state.mood,
                    "energy": state.energy,
                    "stress": state.stress,
                    "sleep_hours": state.sleep_hours,
                    "sleep_quality": state.sleep_quality,
                    "focus": state.focus,
                    "motivation": state.motivation,
                    "health": state.health,
                    "notes": state.notes
                }
                export_data["states"].append(state_data)
            
            # 保存到文件
            filename = f"goal_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join("data", filename)
            
            # 确保目录存在
            os.makedirs("data", exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 数据导出成功！")
            print(f"📁 文件位置: {filepath}")
            print(f"📊 导出内容:")
            print(f"   • 目标: {len(export_data['goals'])}个")
            print(f"   • 状态记录: {len(export_data['states'])}条")
            print(f"   • 活动记录: {sum(len(g['activities']) for g in export_data['goals'])}条")
            
        except Exception as e:
            print(f"❌ 导出数据失败: {e}")
    
    def show_goodbye(self):
        """显示告别信息"""
        print("\n" + "=" * 50)
        print("👋 感谢使用智能目标检测系统！")
        print("=" * 50)
        print("记住：")
        print("• 坚持记录是成功的关键")
        print("• 小步快跑，持续改进")
        print("• 相信数据，相信自己")
        print("=" * 50)
        print("期待您的再次使用！🎯")
    
    # 辅助方法
    def create_progress_bar(self, progress: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {progress:.1%}"
    
    def get_int_input(self, prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
        """获取整数输入"""
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    return default
                
                result = int(value)
                
                if min_val is not None and result < min_val:
                    print(f"❌ 值不能小于 {min_val}")
                    continue
                
                if max_val is not None and result > max_val:
                    print(f"❌ 值不能大于 {max_val}")
                    continue
                
                return result
                
            except ValueError:
                print("❌ 请输入有效的整数")
    
    def get_float_input(self, prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
        """获取浮点数输入"""
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    return default
                
                result = float(value)
                
                if min_val is not None and result < min_val:
                    print(f"❌ 值不能小于 {min_val}")
                    continue
                
                if max_val is not None and result > max_val:
                    print(f"❌ 值不能大于 {max_val}")
                    continue
                
                return result
                
            except ValueError:
                print("❌ 请输入有效的数字")
    
    def show_state_summary(self, state: DailyState):
        """显示状态摘要"""
        print(f"\n📊 今日状态摘要:")
        print(f"   😊 心情: {state.mood}/10")
        print(f"   ⚡ 精力: {state.energy}/10")
        print(f"   😰 压力: {state.stress}/10")
        print(f"   😴 睡眠: {state.sleep_hours}小时 (质量: {state.sleep_quality}/10)")
        print(f"   🎯 专注: {state.focus}/10")
        print(f"   🔥 动机: {state.motivation}/10")
        print(f"   💪 健康: {state.health}/10")
        
        # 简单的状态评估
        avg_score = (state.mood + state.energy + (10 - state.stress) + 
                    state.focus + state.motivation + state.health) / 6
        
        if avg_score >= 8:
            print("🎉 今日状态优秀！")
        elif avg_score >= 6:
            print("👍 今日状态良好")
        elif avg_score >= 4:
            print("😐 今日状态一般")
        else:
            print("😔 今日状态需要关注")
    
    def show_activity_summary(self, activity: DailyActivity):
        """显示活动摘要"""
        print(f"\n📊 活动摘要:")
        print(f"   📝 类型: {activity.activity_type.value}")
        print(f"   ⏱️ 时长: {activity.duration_minutes}分钟")
        print(f"   ⚡ 效率: {activity.efficiency}/10")
        print(f"   📈 进度: {activity.progress}%")
        print(f"   😊 满意度: {activity.satisfaction}/10")
        
        # 简单的活动评估
        if activity.efficiency >= 8 and activity.satisfaction >= 8:
            print("🎉 这是一次高质量的活动！")
        elif activity.efficiency >= 6 and activity.satisfaction >= 6:
            print("👍 活动执行良好")
        else:
            print("💡 下次可以尝试优化执行方式")


def main():
    """主函数"""
    try:
        cli = GoalTrackerCLI()
        cli.run()
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        print("请检查系统配置或联系技术支持")


if __name__ == "__main__":
    main()