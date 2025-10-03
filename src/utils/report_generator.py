"""
可解释性报告生成器
生成详细的预测分析报告，解释影响因素和建议
"""
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from dataclasses import asdict

from ..database.models import Goal, DailyState, DailyActivity, Prediction, GoalCategory
from ..database.database import DatabaseManager


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def generate_prediction_report(self, prediction: Prediction, goal: Goal,
                                 include_charts: bool = True) -> Dict[str, Any]:
        """生成预测报告"""
        report = {
            "report_id": f"report_{prediction.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "goal_info": self._get_goal_summary(goal),
            "prediction_summary": self._get_prediction_summary(prediction),
            "factor_analysis": self._analyze_key_factors(prediction, goal),
            "recommendations": self._format_recommendations(prediction.recommendations),
            "confidence_analysis": self._analyze_confidence(prediction, goal),
            "historical_context": self._get_historical_context(goal),
            "risk_assessment": self._assess_risks(prediction, goal),
            "action_plan": self._generate_action_plan(prediction, goal)
        }
        
        if include_charts:
            report["charts"] = self._generate_charts(prediction, goal)
        
        return report
    
    def generate_comprehensive_report(self, goals: List[Goal]) -> Dict[str, Any]:
        """生成综合报告"""
        report = {
            "report_type": "comprehensive",
            "generated_at": datetime.now().isoformat(),
            "overview": self._get_overview(goals),
            "goal_analysis": [],
            "trends": self._analyze_trends(),
            "patterns": self._identify_patterns(),
            "recommendations": self._get_global_recommendations(goals),
            "data_quality": self._assess_data_quality()
        }
        
        # 为每个目标生成分析
        for goal in goals:
            latest_prediction = self.db.get_latest_prediction(goal.id)
            if latest_prediction:
                goal_analysis = {
                    "goal": self._get_goal_summary(goal),
                    "prediction": self._get_prediction_summary(latest_prediction),
                    "status": self._get_goal_status(goal, latest_prediction)
                }
                report["goal_analysis"].append(goal_analysis)
        
        return report
    
    def _get_goal_summary(self, goal: Goal) -> Dict[str, Any]:
        """获取目标摘要"""
        return {
            "id": goal.id,
            "name": goal.name,
            "category": goal.category.value,
            "description": goal.description,
            "target_value": goal.target_value,
            "current_value": goal.current_value,
            "completion_rate": goal.current_value / goal.target_value if goal.target_value > 0 else 0,
            "unit": goal.unit,
            "priority": goal.priority,
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
            "days_remaining": (goal.deadline - datetime.now()).days if goal.deadline else None,
            "created_at": goal.created_at.isoformat() if goal.created_at else None
        }
    
    def _get_prediction_summary(self, prediction: Prediction) -> Dict[str, Any]:
        """获取预测摘要"""
        return {
            "success_probability": prediction.success_probability,
            "success_level": self._categorize_success_probability(prediction.success_probability),
            "productivity_score": prediction.productivity_score,
            "productivity_level": self._categorize_productivity_score(prediction.productivity_score),
            "model_type": prediction.model_type,
            "confidence": prediction.confidence,
            "confidence_level": self._categorize_confidence(prediction.confidence),
            "prediction_date": prediction.prediction_date.isoformat(),
            "target_date": prediction.target_date.isoformat()
        }
    
    def _analyze_key_factors(self, prediction: Prediction, goal: Goal) -> Dict[str, Any]:
        """分析关键影响因素"""
        factors = prediction.key_factors
        
        # 按影响程度排序
        sorted_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)
        
        analysis = {
            "top_positive_factors": [],
            "top_negative_factors": [],
            "factor_explanations": {},
            "improvement_potential": {}
        }
        
        for factor, weight in sorted_factors:
            explanation = self._explain_factor(factor, weight)
            analysis["factor_explanations"][factor] = explanation
            
            if weight > 0.1:  # 正向影响
                analysis["top_positive_factors"].append({
                    "factor": factor,
                    "weight": weight,
                    "impact": "积极",
                    "explanation": explanation
                })
            elif weight < -0.1:  # 负向影响
                analysis["top_negative_factors"].append({
                    "factor": factor,
                    "weight": abs(weight),
                    "impact": "消极",
                    "explanation": explanation
                })
            
            # 改进潜力分析
            if weight < 0.6:  # 有改进空间
                analysis["improvement_potential"][factor] = {
                    "current_score": weight,
                    "potential_improvement": min(1.0 - weight, 0.4),
                    "priority": "高" if weight < 0.4 else "中" if weight < 0.6 else "低"
                }
        
        return analysis
    
    def _format_recommendations(self, recommendations: List[str]) -> List[Dict[str, Any]]:
        """格式化建议"""
        formatted_recs = []
        
        for i, rec in enumerate(recommendations):
            # 解析建议类型和内容
            category = "通用建议"
            priority = "中"
            
            if "睡眠" in rec:
                category = "睡眠优化"
                priority = "高"
            elif "运动" in rec or "健身" in rec:
                category = "运动健康"
                priority = "中"
            elif "压力" in rec:
                category = "压力管理"
                priority = "高"
            elif "效率" in rec:
                category = "效率提升"
                priority = "高"
            elif "时间" in rec:
                category = "时间管理"
                priority = "中"
            elif "动机" in rec or "目标" in rec:
                category = "动机激励"
                priority = "中"
            
            formatted_recs.append({
                "id": i + 1,
                "category": category,
                "content": rec,
                "priority": priority,
                "actionable": self._is_actionable(rec),
                "estimated_impact": self._estimate_impact(rec)
            })
        
        return formatted_recs
    
    def _analyze_confidence(self, prediction: Prediction, goal: Goal) -> Dict[str, Any]:
        """分析预测置信度"""
        confidence = prediction.confidence
        
        # 获取数据质量指标
        recent_states = self.db.get_recent_states(30)
        goal_activities = self.db.get_goal_activities(goal.id, 30)
        
        analysis = {
            "confidence_score": confidence,
            "confidence_level": self._categorize_confidence(confidence),
            "data_quality": {
                "state_records": len(recent_states),
                "activity_records": len(goal_activities),
                "data_freshness": self._calculate_data_freshness(recent_states, goal_activities),
                "data_completeness": self._calculate_data_completeness(recent_states, goal_activities)
            },
            "reliability_factors": [],
            "limitations": []
        }
        
        # 可靠性因素
        if len(recent_states) >= 14:
            analysis["reliability_factors"].append("状态数据充足")
        else:
            analysis["limitations"].append("状态数据不足，可能影响预测准确性")
        
        if len(goal_activities) >= 21:
            analysis["reliability_factors"].append("活动数据丰富")
        else:
            analysis["limitations"].append("活动数据较少，建议增加记录频率")
        
        if prediction.model_type == "ml":
            analysis["reliability_factors"].append("使用机器学习模型，预测更准确")
        elif prediction.model_type == "ai":
            analysis["reliability_factors"].append("结合AI分析，考虑更多复杂因素")
        else:
            analysis["limitations"].append("使用启发式规则，准确性有限")
        
        return analysis
    
    def _get_historical_context(self, goal: Goal) -> Dict[str, Any]:
        """获取历史背景"""
        # 获取历史预测
        prediction_history = self.db.get_prediction_history(goal.id, 10)
        
        # 获取历史活动趋势
        activities = self.db.get_goal_activities(goal.id, 60)
        
        context = {
            "prediction_trend": self._analyze_prediction_trend(prediction_history),
            "performance_trend": self._analyze_performance_trend(activities),
            "consistency_pattern": self._analyze_consistency_pattern(activities),
            "seasonal_effects": self._identify_seasonal_effects(activities)
        }
        
        return context
    
    def _assess_risks(self, prediction: Prediction, goal: Goal) -> Dict[str, Any]:
        """评估风险"""
        risks = {
            "high_risks": [],
            "medium_risks": [],
            "low_risks": [],
            "mitigation_strategies": {}
        }
        
        # 基于成功概率评估风险
        if prediction.success_probability < 0.3:
            risks["high_risks"].append({
                "type": "目标达成风险",
                "description": "成功概率较低，需要重新评估目标或调整策略",
                "probability": "高"
            })
        elif prediction.success_probability < 0.6:
            risks["medium_risks"].append({
                "type": "目标达成风险",
                "description": "成功概率中等，需要加强执行力度",
                "probability": "中"
            })
        
        # 基于时间压力评估风险
        if goal.deadline:
            days_left = (goal.deadline - datetime.now()).days
            if days_left <= 7:
                risks["high_risks"].append({
                    "type": "时间压力风险",
                    "description": "截止日期临近，时间非常紧迫",
                    "probability": "高"
                })
            elif days_left <= 30:
                risks["medium_risks"].append({
                    "type": "时间压力风险",
                    "description": "时间相对紧张，需要合理安排",
                    "probability": "中"
                })
        
        # 基于关键因素评估风险
        for factor, weight in prediction.key_factors.items():
            if weight < 0.4:
                risk_type = f"{factor}不足风险"
                risks["medium_risks"].append({
                    "type": risk_type,
                    "description": f"{factor}水平较低，可能影响目标达成",
                    "probability": "中"
                })
        
        # 生成缓解策略
        for risk_list in [risks["high_risks"], risks["medium_risks"]]:
            for risk in risk_list:
                risks["mitigation_strategies"][risk["type"]] = self._generate_mitigation_strategy(risk)
        
        return risks
    
    def _generate_action_plan(self, prediction: Prediction, goal: Goal) -> Dict[str, Any]:
        """生成行动计划"""
        plan = {
            "immediate_actions": [],  # 立即行动
            "short_term_actions": [],  # 短期行动（1-2周）
            "long_term_actions": [],  # 长期行动（1个月以上）
            "milestones": [],
            "review_schedule": {}
        }
        
        # 基于建议生成行动项
        for rec in prediction.recommendations:
            action = self._convert_recommendation_to_action(rec)
            
            if "立即" in rec or "紧急" in rec:
                plan["immediate_actions"].append(action)
            elif "每日" in rec or "每天" in rec:
                plan["short_term_actions"].append(action)
            else:
                plan["long_term_actions"].append(action)
        
        # 设置里程碑
        if goal.deadline:
            days_left = (goal.deadline - datetime.now()).days
            if days_left > 30:
                milestone_dates = [
                    datetime.now() + timedelta(days=7),
                    datetime.now() + timedelta(days=21),
                    goal.deadline - timedelta(days=7)
                ]
            elif days_left > 14:
                milestone_dates = [
                    datetime.now() + timedelta(days=7),
                    goal.deadline - timedelta(days=3)
                ]
            else:
                milestone_dates = [goal.deadline - timedelta(days=1)]
            
            for i, milestone_date in enumerate(milestone_dates):
                plan["milestones"].append({
                    "id": i + 1,
                    "date": milestone_date.isoformat(),
                    "description": f"检查点{i + 1}：评估进度和调整策略",
                    "target_completion": min(1.0, (i + 1) / len(milestone_dates))
                })
        
        # 设置复查计划
        plan["review_schedule"] = {
            "daily_review": "每日记录状态和活动",
            "weekly_review": "每周评估进度和调整计划",
            "monthly_review": "每月重新预测和优化策略"
        }
        
        return plan
    
    def _generate_charts(self, prediction: Prediction, goal: Goal) -> Dict[str, str]:
        """生成图表"""
        charts = {}
        
        try:
            # 1. 关键因素雷达图
            charts["factors_radar"] = self._create_factors_radar_chart(prediction.key_factors)
            
            # 2. 历史趋势图
            charts["trend_chart"] = self._create_trend_chart(goal)
            
            # 3. 预测置信度图
            charts["confidence_chart"] = self._create_confidence_chart(prediction)
            
        except Exception as e:
            print(f"生成图表失败: {e}")
        
        return charts
    
    def _create_factors_radar_chart(self, factors: Dict[str, float]) -> str:
        """创建因素雷达图"""
        if not factors:
            return ""
        
        # 准备数据
        categories = list(factors.keys())
        values = list(factors.values())
        
        # 创建雷达图
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
        values += values[:1]  # 闭合图形
        angles = np.concatenate((angles, [angles[0]]))
        
        # 绘制
        ax.plot(angles, values, 'o-', linewidth=2, label='当前水平')
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('关键影响因素分析', size=16, pad=20)
        
        # 保存图表
        chart_path = f"charts/factors_radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_trend_chart(self, goal: Goal) -> str:
        """创建趋势图"""
        activities = self.db.get_goal_activities(goal.id, 30)
        
        if not activities:
            return ""
        
        # 准备数据
        df = pd.DataFrame([{
            'date': act.date,
            'efficiency': act.efficiency,
            'progress': act.progress,
            'satisfaction': act.satisfaction
        } for act in activities if act.date])
        
        if df.empty:
            return ""
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 创建图表
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 效率趋势
        axes[0].plot(df['date'], df['efficiency'], marker='o', label='执行效率')
        axes[0].set_title('执行效率趋势')
        axes[0].set_ylabel('效率评分')
        axes[0].grid(True, alpha=0.3)
        
        # 进度趋势
        axes[1].plot(df['date'], df['progress'], marker='s', color='green', label='完成进度')
        axes[1].set_title('完成进度趋势')
        axes[1].set_ylabel('进度百分比')
        axes[1].grid(True, alpha=0.3)
        
        # 满意度趋势
        axes[2].plot(df['date'], df['satisfaction'], marker='^', color='orange', label='满意度')
        axes[2].set_title('满意度趋势')
        axes[2].set_ylabel('满意度评分')
        axes[2].set_xlabel('日期')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = f"charts/trend_{goal.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_confidence_chart(self, prediction: Prediction) -> str:
        """创建置信度图表"""
        # 创建置信度可视化
        fig, ax = plt.subplots(figsize=(8, 6))
        
        confidence = prediction.confidence
        success_prob = prediction.success_probability
        
        # 创建置信度条形图
        categories = ['预测置信度', '成功概率', '生产力评分/10']
        values = [confidence, success_prob, prediction.productivity_score / 10]
        colors = ['blue', 'green', 'orange']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{value:.2f}', ha='center', va='bottom')
        
        ax.set_ylim(0, 1.1)
        ax.set_title('预测结果概览')
        ax.set_ylabel('评分')
        
        # 保存图表
        chart_path = f"charts/confidence_{prediction.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    # 辅助方法
    def _categorize_success_probability(self, prob: float) -> str:
        """分类成功概率"""
        if prob >= 0.8:
            return "很高"
        elif prob >= 0.6:
            return "较高"
        elif prob >= 0.4:
            return "中等"
        elif prob >= 0.2:
            return "较低"
        else:
            return "很低"
    
    def _categorize_productivity_score(self, score: float) -> str:
        """分类生产力评分"""
        if score >= 8:
            return "优秀"
        elif score >= 6:
            return "良好"
        elif score >= 4:
            return "一般"
        else:
            return "需改进"
    
    def _categorize_confidence(self, confidence: float) -> str:
        """分类置信度"""
        if confidence >= 0.8:
            return "高"
        elif confidence >= 0.6:
            return "中"
        else:
            return "低"
    
    def _explain_factor(self, factor: str, weight: float) -> str:
        """解释因素"""
        explanations = {
            "心情状态": "心情好坏直接影响执行动力和效率",
            "精力水平": "充沛的精力是完成任务的基础",
            "压力水平": "适度压力有助于专注，过高压力会影响表现",
            "睡眠质量": "良好睡眠保证次日的精力和专注度",
            "专注度": "专注能力决定任务执行的质量和效率",
            "动机水平": "强烈的动机是坚持目标的核心驱动力",
            "执行效率": "高效执行能够在有限时间内完成更多任务",
            "行动一致性": "持续稳定的行动是达成目标的关键",
            "目标完成度": "当前进度反映了目标实现的可能性"
        }
        
        base_explanation = explanations.get(factor, f"{factor}对目标达成有重要影响")
        
        if weight > 0.7:
            return f"{base_explanation}，当前表现优秀"
        elif weight > 0.5:
            return f"{base_explanation}，当前表现良好"
        elif weight > 0.3:
            return f"{base_explanation}，当前表现一般，有改进空间"
        else:
            return f"{base_explanation}，当前表现较差，需要重点改进"
    
    def _is_actionable(self, recommendation: str) -> bool:
        """判断建议是否可执行"""
        actionable_keywords = ["建议", "可以", "应该", "尝试", "制定", "设置", "安排"]
        return any(keyword in recommendation for keyword in actionable_keywords)
    
    def _estimate_impact(self, recommendation: str) -> str:
        """估计建议的影响程度"""
        high_impact_keywords = ["睡眠", "压力", "效率", "动机"]
        medium_impact_keywords = ["心情", "专注", "时间", "计划"]
        
        if any(keyword in recommendation for keyword in high_impact_keywords):
            return "高"
        elif any(keyword in recommendation for keyword in medium_impact_keywords):
            return "中"
        else:
            return "低"
    
    def _calculate_data_freshness(self, states: List[DailyState], 
                                activities: List[DailyActivity]) -> float:
        """计算数据新鲜度"""
        if not states and not activities:
            return 0.0
        
        latest_date = date.today()
        if states:
            latest_state_date = max(s.date for s in states)
            latest_date = min(latest_date, latest_state_date)
        
        if activities:
            latest_activity_date = max(a.date for a in activities if a.date)
            latest_date = min(latest_date, latest_activity_date)
        
        days_since_latest = (date.today() - latest_date).days
        return max(0.0, 1.0 - days_since_latest / 7.0)  # 7天内为新鲜
    
    def _calculate_data_completeness(self, states: List[DailyState], 
                                   activities: List[DailyActivity]) -> float:
        """计算数据完整性"""
        # 简单的完整性评估：最近30天的数据覆盖率
        expected_days = 30
        state_days = len(set(s.date for s in states)) if states else 0
        activity_days = len(set(a.date for a in activities if a.date)) if activities else 0
        
        state_completeness = min(state_days / expected_days, 1.0)
        activity_completeness = min(activity_days / expected_days, 1.0)
        
        return (state_completeness + activity_completeness) / 2
    
    def _analyze_prediction_trend(self, predictions: List[Prediction]) -> Dict[str, Any]:
        """分析预测趋势"""
        if len(predictions) < 2:
            return {"trend": "数据不足", "change": 0}
        
        # 按时间排序
        sorted_predictions = sorted(predictions, key=lambda p: p.prediction_date)
        
        # 计算趋势
        recent_prob = sorted_predictions[-1].success_probability
        previous_prob = sorted_predictions[-2].success_probability
        change = recent_prob - previous_prob
        
        trend = "上升" if change > 0.05 else "下降" if change < -0.05 else "稳定"
        
        return {
            "trend": trend,
            "change": change,
            "recent_probability": recent_prob,
            "previous_probability": previous_prob
        }
    
    def _analyze_performance_trend(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析表现趋势"""
        if len(activities) < 7:
            return {"trend": "数据不足"}
        
        # 按日期排序
        sorted_activities = sorted([a for a in activities if a.date], key=lambda a: a.date)
        
        # 计算最近一周和前一周的平均表现
        recent_week = sorted_activities[-7:]
        previous_week = sorted_activities[-14:-7] if len(sorted_activities) >= 14 else []
        
        recent_avg = sum(a.efficiency for a in recent_week) / len(recent_week)
        
        if previous_week:
            previous_avg = sum(a.efficiency for a in previous_week) / len(previous_week)
            change = recent_avg - previous_avg
            trend = "改善" if change > 0.5 else "下降" if change < -0.5 else "稳定"
        else:
            trend = "数据不足"
            change = 0
        
        return {
            "trend": trend,
            "change": change,
            "recent_average": recent_avg
        }
    
    def _analyze_consistency_pattern(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析一致性模式"""
        if not activities:
            return {"pattern": "无数据"}
        
        # 按星期几分组
        weekday_counts = {}
        for activity in activities:
            if activity.date:
                weekday = activity.date.weekday()
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
        
        # 找出最活跃的日子
        if weekday_counts:
            most_active_day = max(weekday_counts, key=weekday_counts.get)
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            
            return {
                "pattern": f"最活跃：{weekday_names[most_active_day]}",
                "weekday_distribution": weekday_counts,
                "consistency_score": len(weekday_counts) / 7.0  # 一周中活跃天数的比例
            }
        
        return {"pattern": "无明显模式"}
    
    def _identify_seasonal_effects(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """识别季节性影响"""
        # 简化的季节性分析
        if len(activities) < 30:
            return {"effects": "数据不足"}
        
        # 按月份分组分析效率
        monthly_efficiency = {}
        for activity in activities:
            if activity.date:
                month = activity.date.month
                if month not in monthly_efficiency:
                    monthly_efficiency[month] = []
                monthly_efficiency[month].append(activity.efficiency)
        
        # 计算每月平均效率
        monthly_avg = {}
        for month, efficiencies in monthly_efficiency.items():
            monthly_avg[month] = sum(efficiencies) / len(efficiencies)
        
        if len(monthly_avg) >= 2:
            best_month = max(monthly_avg, key=monthly_avg.get)
            worst_month = min(monthly_avg, key=monthly_avg.get)
            
            month_names = ["", "1月", "2月", "3月", "4月", "5月", "6月",
                          "7月", "8月", "9月", "10月", "11月", "12月"]
            
            return {
                "effects": f"表现最佳：{month_names[best_month]}，最差：{month_names[worst_month]}",
                "monthly_averages": monthly_avg
            }
        
        return {"effects": "无明显季节性影响"}
    
    def _generate_mitigation_strategy(self, risk: Dict[str, Any]) -> str:
        """生成风险缓解策略"""
        risk_type = risk["type"]
        
        strategies = {
            "目标达成风险": "重新评估目标的现实性，分解为更小的子目标，增加执行频率",
            "时间压力风险": "优先处理核心任务，暂时搁置非关键活动，寻求外部支持",
            "动机水平不足风险": "重新审视目标意义，设置奖励机制，寻找执行伙伴",
            "精力水平不足风险": "优化作息时间，改善营养状况，适当减少其他消耗",
            "压力水平过高风险": "学习压力管理技巧，适当降低期望，寻求专业帮助"
        }
        
        return strategies.get(risk_type, "制定针对性的改进计划，定期监控和调整")
    
    def _convert_recommendation_to_action(self, recommendation: str) -> Dict[str, Any]:
        """将建议转换为行动项"""
        return {
            "description": recommendation,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": "中",
            "status": "待执行",
            "estimated_time": "30分钟/天"
        }
    
    # 综合报告相关方法
    def _get_overview(self, goals: List[Goal]) -> Dict[str, Any]:
        """获取概览"""
        if not goals:
            return {"message": "暂无活跃目标"}
        
        total_goals = len(goals)
        completed_goals = sum(1 for g in goals if g.current_value >= g.target_value and g.target_value > 0)
        avg_completion = sum(g.current_value / g.target_value if g.target_value > 0 else 0 for g in goals) / total_goals
        
        return {
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "in_progress_goals": total_goals - completed_goals,
            "average_completion_rate": avg_completion,
            "categories": list(set(g.category.value for g in goals))
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """分析整体趋势"""
        recent_states = self.db.get_recent_states(30)
        
        if len(recent_states) < 7:
            return {"message": "数据不足"}
        
        # 计算趋势
        recent_week = recent_states[:7]
        previous_week = recent_states[7:14] if len(recent_states) >= 14 else []
        
        trends = {}
        
        for metric in ['mood', 'energy', 'stress', 'focus', 'motivation']:
            recent_avg = sum(getattr(s, metric) for s in recent_week) / len(recent_week)
            
            if previous_week:
                previous_avg = sum(getattr(s, metric) for s in previous_week) / len(previous_week)
                change = recent_avg - previous_avg
                trend = "上升" if change > 0.5 else "下降" if change < -0.5 else "稳定"
            else:
                trend = "数据不足"
                change = 0
            
            trends[metric] = {
                "trend": trend,
                "change": change,
                "current_level": recent_avg
            }
        
        return trends
    
    def _identify_patterns(self) -> Dict[str, Any]:
        """识别模式"""
        # 获取所有活动数据
        all_activities = []
        active_goals = self.db.get_active_goals()
        
        for goal in active_goals:
            activities = self.db.get_goal_activities(goal.id, 60)
            all_activities.extend(activities)
        
        if not all_activities:
            return {"message": "暂无活动数据"}
        
        # 分析模式
        patterns = {
            "most_productive_day": self._find_most_productive_day(all_activities),
            "optimal_duration": self._find_optimal_duration(all_activities),
            "efficiency_patterns": self._analyze_efficiency_patterns(all_activities)
        }
        
        return patterns
    
    def _get_global_recommendations(self, goals: List[Goal]) -> List[str]:
        """获取全局建议"""
        recommendations = []
        
        if not goals:
            return ["建议：设置第一个目标开始你的改变之旅"]
        
        # 基于目标数量的建议
        if len(goals) > 5:
            recommendations.append("建议：目标较多，建议专注于2-3个最重要的目标")
        
        # 基于完成率的建议
        avg_completion = sum(g.current_value / g.target_value if g.target_value > 0 else 0 for g in goals) / len(goals)
        if avg_completion < 0.3:
            recommendations.append("建议：整体进度较慢，考虑调整目标难度或增加执行时间")
        elif avg_completion > 0.8:
            recommendations.append("建议：进度良好，可以考虑设置更有挑战性的目标")
        
        # 基于截止日期的建议
        urgent_goals = [g for g in goals if g.deadline and (g.deadline - datetime.now()).days <= 7]
        if urgent_goals:
            recommendations.append(f"提醒：有{len(urgent_goals)}个目标即将到期，需要优先处理")
        
        return recommendations
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """评估数据质量"""
        summary = self.db.get_data_summary()
        
        quality_score = 0
        issues = []
        strengths = []
        
        # 评估数据量
        if summary['state_records'] >= 30:
            quality_score += 25
            strengths.append("状态记录充足")
        else:
            issues.append("状态记录不足，建议每日记录")
        
        if summary['activity_records'] >= 50:
            quality_score += 25
            strengths.append("活动记录丰富")
        else:
            issues.append("活动记录较少，建议增加记录频率")
        
        # 评估数据新鲜度
        recent_states = self.db.get_recent_states(7)
        if len(recent_states) >= 5:
            quality_score += 25
            strengths.append("数据更新及时")
        else:
            issues.append("最近数据更新不及时")
        
        # 评估数据完整性
        if summary['active_goals'] > 0:
            quality_score += 25
            strengths.append("有明确的目标设定")
        else:
            issues.append("缺少明确的目标设定")
        
        return {
            "quality_score": quality_score,
            "level": "优秀" if quality_score >= 80 else "良好" if quality_score >= 60 else "需改进",
            "strengths": strengths,
            "issues": issues,
            "recommendations": [
                "建议每日记录状态和活动",
                "设置明确的目标和截止日期",
                "定期回顾和更新数据"
            ]
        }
    
    def _get_goal_status(self, goal: Goal, prediction: Prediction) -> str:
        """获取目标状态"""
        completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
        
        if completion_rate >= 1.0:
            return "已完成"
        elif prediction.success_probability >= 0.7:
            return "进展良好"
        elif prediction.success_probability >= 0.4:
            return "需要努力"
        else:
            return "面临挑战"
    
    def _find_most_productive_day(self, activities: List[DailyActivity]) -> str:
        """找出最高效的日子"""
        if not activities:
            return "数据不足"
        
        weekday_efficiency = {}
        for activity in activities:
            if activity.date:
                weekday = activity.date.weekday()
                if weekday not in weekday_efficiency:
                    weekday_efficiency[weekday] = []
                weekday_efficiency[weekday].append(activity.efficiency)
        
        # 计算平均效率
        weekday_avg = {}
        for weekday, efficiencies in weekday_efficiency.items():
            weekday_avg[weekday] = sum(efficiencies) / len(efficiencies)
        
        if weekday_avg:
            best_day = max(weekday_avg, key=weekday_avg.get)
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            return weekday_names[best_day]
        
        return "无明显模式"
    
    def _find_optimal_duration(self, activities: List[DailyActivity]) -> str:
        """找出最佳持续时间"""
        if not activities:
            return "数据不足"
        
        # 按持续时间分组
        duration_efficiency = {}
        for activity in activities:
            duration_range = self._get_duration_range(activity.duration_minutes)
            if duration_range not in duration_efficiency:
                duration_efficiency[duration_range] = []
            duration_efficiency[duration_range].append(activity.efficiency)
        
        # 找出效率最高的时间段
        best_range = None
        best_efficiency = 0
        
        for duration_range, efficiencies in duration_efficiency.items():
            avg_efficiency = sum(efficiencies) / len(efficiencies)
            if avg_efficiency > best_efficiency:
                best_efficiency = avg_efficiency
                best_range = duration_range
        
        return best_range or "无明显模式"
    
    def _get_duration_range(self, minutes: int) -> str:
        """获取持续时间范围"""
        if minutes <= 30:
            return "30分钟以内"
        elif minutes <= 60:
            return "30-60分钟"
        elif minutes <= 120:
            return "1-2小时"
        else:
            return "2小时以上"
    
    def _analyze_efficiency_patterns(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析效率模式"""
        if not activities:
            return {"message": "数据不足"}
        
        # 按活动类型分析效率
        type_efficiency = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            if activity_type not in type_efficiency:
                type_efficiency[activity_type] = []
            type_efficiency[activity_type].append(activity.efficiency)
        
        # 计算平均效率
        type_avg = {}
        for activity_type, efficiencies in type_efficiency.items():
            type_avg[activity_type] = sum(efficiencies) / len(efficiencies)
        
        # 找出最高效和最低效的活动类型
        if type_avg:
            most_efficient = max(type_avg, key=type_avg.get)
            least_efficient = min(type_avg, key=type_avg.get)
            
            return {
                "most_efficient_type": most_efficient,
                "least_efficient_type": least_efficient,
                "type_averages": type_avg
            }
        
        return {"message": "无明显模式"}
    
    def export_report_to_json(self, report: Dict[str, Any], filename: str = None) -> str:
        """导出报告为JSON文件"""
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = f"reports/{filename}"
        
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath