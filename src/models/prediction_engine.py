"""
核心预测引擎
整合启发式、机器学习和AI预测方法
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

from ..database.models import Goal, DailyState, DailyActivity, Prediction
from ..database.database import DatabaseManager
from .heuristic_engine import HeuristicEngine
from .ml_predictor import MLPredictor
from ..api.deepseek_client import DeepSeekClient, AIPredictor
from ..utils.report_generator import ReportGenerator


class PredictionEngine:
    """核心预测引擎"""
    
    def __init__(self, db_manager: DatabaseManager, deepseek_api_key: str = None):
        self.db = db_manager
        
        # 初始化各种预测器
        self.heuristic_engine = HeuristicEngine(db_manager)
        self.ml_predictor = MLPredictor(db_manager)
        
        # 初始化AI预测器（可选）
        self.deepseek_client = DeepSeekClient(deepseek_api_key)
        self.ai_predictor = AIPredictor(db_manager, self.deepseek_client) if deepseek_api_key else None
        
        # 初始化报告生成器
        self.report_generator = ReportGenerator(db_manager)
        
        # 预测策略配置
        self.prediction_strategy = "auto"  # auto, heuristic, ml, ai
        self.min_data_for_ml = 30  # ML模型需要的最少数据量
    
    def predict_goal_success(self, goal: Goal, target_date: datetime = None,
                           strategy: str = None, include_report: bool = True) -> Dict[str, Any]:
        """预测目标成功率"""
        if target_date is None:
            target_date = goal.deadline or datetime.now() + timedelta(days=30)
        
        strategy = strategy or self.prediction_strategy
        
        # 获取基础数据
        recent_states = self.db.get_recent_states(30)
        goal_activities = self.db.get_goal_activities(goal.id, 30)
        
        # 选择预测方法
        prediction = None
        method_used = "heuristic"
        
        if strategy == "auto":
            prediction, method_used = self._auto_select_prediction_method(
                goal, target_date, recent_states, goal_activities
            )
        elif strategy == "heuristic":
            prediction = self.heuristic_engine.predict_goal_success(goal, target_date)
            method_used = "heuristic"
        elif strategy == "ml" and self.ml_predictor.is_model_available():
            prediction = self.ml_predictor.predict_goal_success(goal, target_date)
            method_used = "ml" if prediction else "heuristic"
            if not prediction:  # ML失败，回退到启发式
                prediction = self.heuristic_engine.predict_goal_success(goal, target_date)
        elif strategy == "ai" and self.ai_predictor:
            prediction = self.ai_predictor.predict_goal_success(goal, target_date)
            method_used = "ai" if prediction else "heuristic"
            if not prediction:  # AI失败，回退到启发式
                prediction = self.heuristic_engine.predict_goal_success(goal, target_date)
        else:
            # 默认使用启发式
            prediction = self.heuristic_engine.predict_goal_success(goal, target_date)
            method_used = "heuristic"
        
        if not prediction:
            raise ValueError("预测失败，无法生成预测结果")
        
        # 增强建议（如果有AI）
        if self.ai_predictor and method_used != "ai":
            enhanced_recommendations = self.ai_predictor.get_enhanced_recommendations(goal, prediction)
            prediction.recommendations = enhanced_recommendations
        
        # 保存预测结果
        prediction_id = self.db.save_prediction(prediction)
        prediction.id = prediction_id
        
        # 构建返回结果
        result = {
            "prediction": {
                "id": prediction.id,
                "goal_id": prediction.goal_id,
                "success_probability": prediction.success_probability,
                "productivity_score": prediction.productivity_score,
                "confidence": prediction.confidence,
                "model_type": prediction.model_type,
                "method_used": method_used,
                "key_factors": prediction.key_factors,
                "recommendations": prediction.recommendations,
                "prediction_date": prediction.prediction_date.isoformat(),
                "target_date": prediction.target_date.isoformat()
            },
            "summary": self._generate_prediction_summary(prediction, goal),
            "data_quality": self._assess_prediction_data_quality(recent_states, goal_activities)
        }
        
        # 生成详细报告
        if include_report:
            try:
                detailed_report = self.report_generator.generate_prediction_report(prediction, goal)
                result["detailed_report"] = detailed_report
            except Exception as e:
                print(f"生成详细报告失败: {e}")
                result["detailed_report"] = None
        
        return result
    
    def predict_weekly_productivity(self, target_date: datetime = None) -> Dict[str, Any]:
        """预测未来一周的生产力"""
        if target_date is None:
            target_date = datetime.now() + timedelta(days=7)
        
        # 使用启发式方法预测每日生产力
        daily_predictions = self.heuristic_engine.predict_weekly_productivity(target_date)
        
        # 计算周平均生产力
        if daily_predictions:
            avg_productivity = sum(daily_predictions.values()) / len(daily_predictions)
            max_day = max(daily_predictions, key=daily_predictions.get)
            min_day = min(daily_predictions, key=daily_predictions.get)
        else:
            avg_productivity = 5.0
            max_day = min_day = None
        
        return {
            "target_week": target_date.strftime('%Y-%m-%d'),
            "average_productivity": avg_productivity,
            "daily_predictions": daily_predictions,
            "insights": {
                "highest_productivity_day": max_day,
                "lowest_productivity_day": min_day,
                "productivity_level": self._categorize_productivity(avg_productivity)
            },
            "recommendations": self._generate_weekly_recommendations(daily_predictions)
        }
    
    def analyze_goal_patterns(self, goal: Goal, days: int = 60) -> Dict[str, Any]:
        """分析目标的行为模式"""
        activities = self.db.get_goal_activities(goal.id, days)
        states = self.db.get_recent_states(days)
        
        if not activities:
            return {"message": "数据不足，无法分析模式"}
        
        patterns = {
            "activity_frequency": self._analyze_activity_frequency(activities),
            "efficiency_trends": self._analyze_efficiency_trends(activities),
            "correlation_with_states": self._analyze_state_correlations(activities, states),
            "optimal_conditions": self._identify_optimal_conditions(activities, states),
            "improvement_opportunities": self._identify_improvement_opportunities(activities, states)
        }
        
        return patterns
    
    def get_comprehensive_insights(self) -> Dict[str, Any]:
        """获取综合洞察"""
        active_goals = self.db.get_active_goals()
        
        if not active_goals:
            return {"message": "暂无活跃目标"}
        
        insights = {
            "overview": self._get_system_overview(),
            "goal_insights": [],
            "global_patterns": self._analyze_global_patterns(),
            "recommendations": self._generate_global_recommendations(),
            "data_health": self._assess_system_data_health()
        }
        
        # 为每个目标生成洞察
        for goal in active_goals[:5]:  # 限制最多5个目标
            latest_prediction = self.db.get_latest_prediction(goal.id)
            goal_insight = {
                "goal": {
                    "id": goal.id,
                    "name": goal.name,
                    "category": goal.category.value,
                    "completion_rate": goal.current_value / goal.target_value if goal.target_value > 0 else 0
                },
                "status": self._get_goal_status(goal, latest_prediction),
                "key_insights": self._get_goal_key_insights(goal, latest_prediction)
            }
            insights["goal_insights"].append(goal_insight)
        
        return insights
    
    def train_ml_model(self) -> Dict[str, Any]:
        """训练机器学习模型"""
        if not self.ml_predictor:
            return {"success": False, "message": "ML预测器未初始化"}
        
        try:
            # 检查是否需要重新训练
            if not self.ml_predictor.should_retrain() and self.ml_predictor.is_model_available():
                return {
                    "success": True,
                    "message": "模型已是最新，无需重新训练",
                    "model_available": True
                }
            
            # 训练模型
            metrics = self.ml_predictor.train_models()
            
            if metrics:
                return {
                    "success": True,
                    "message": "模型训练成功",
                    "metrics": metrics,
                    "model_available": True
                }
            else:
                return {
                    "success": False,
                    "message": "模型训练失败，数据可能不足",
                    "model_available": False
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"模型训练出错: {str(e)}",
                "model_available": False
            }
    
    def _auto_select_prediction_method(self, goal: Goal, target_date: datetime,
                                     states: List[DailyState], 
                                     activities: List[DailyActivity]) -> tuple[Prediction, str]:
        """自动选择最佳预测方法"""
        data_quality_score = self._calculate_data_quality_score(states, activities)
        
        # 优先级：AI > ML > 启发式
        if self.ai_predictor and data_quality_score >= 0.6:
            ai_prediction = self.ai_predictor.predict_goal_success(goal, target_date)
            if ai_prediction:
                return ai_prediction, "ai"
        
        if (self.ml_predictor.is_model_available() and 
            len(states) >= 14 and len(activities) >= 21):
            ml_prediction = self.ml_predictor.predict_goal_success(goal, target_date)
            if ml_prediction:
                return ml_prediction, "ml"
        
        # 回退到启发式方法
        heuristic_prediction = self.heuristic_engine.predict_goal_success(goal, target_date)
        return heuristic_prediction, "heuristic"
    
    def _calculate_data_quality_score(self, states: List[DailyState], 
                                    activities: List[DailyActivity]) -> float:
        """计算数据质量评分"""
        score = 0.0
        
        # 状态数据质量
        if len(states) >= 14:
            score += 0.3
        elif len(states) >= 7:
            score += 0.15
        
        # 活动数据质量
        if len(activities) >= 21:
            score += 0.3
        elif len(activities) >= 10:
            score += 0.15
        
        # 数据新鲜度
        if states and (datetime.now().date() - states[0].date).days <= 3:
            score += 0.2
        
        # 数据一致性
        if activities:
            unique_dates = len(set(a.date for a in activities if a.date))
            consistency = unique_dates / min(len(activities), 30)
            score += consistency * 0.2
        
        return min(score, 1.0)
    
    def _generate_prediction_summary(self, prediction: Prediction, goal: Goal) -> Dict[str, Any]:
        """生成预测摘要"""
        return {
            "success_level": self._categorize_success_probability(prediction.success_probability),
            "productivity_level": self._categorize_productivity(prediction.productivity_score),
            "confidence_level": self._categorize_confidence(prediction.confidence),
            "key_message": self._generate_key_message(prediction, goal),
            "priority_actions": prediction.recommendations[:3],  # 前3个最重要的建议
            "risk_level": self._assess_risk_level(prediction, goal)
        }
    
    def _assess_prediction_data_quality(self, states: List[DailyState], 
                                      activities: List[DailyActivity]) -> Dict[str, Any]:
        """评估预测数据质量"""
        return {
            "state_records": len(states),
            "activity_records": len(activities),
            "data_freshness": self._calculate_data_freshness(states, activities),
            "data_completeness": self._calculate_data_completeness(states, activities),
            "quality_score": self._calculate_data_quality_score(states, activities),
            "recommendations": self._generate_data_quality_recommendations(states, activities)
        }
    
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
    
    def _categorize_productivity(self, score: float) -> str:
        """分类生产力水平"""
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
    
    def _generate_key_message(self, prediction: Prediction, goal: Goal) -> str:
        """生成关键信息"""
        success_level = self._categorize_success_probability(prediction.success_probability)
        
        if prediction.success_probability >= 0.7:
            return f"目标'{goal.name}'达成概率{success_level}，继续保持当前节奏"
        elif prediction.success_probability >= 0.4:
            return f"目标'{goal.name}'达成概率{success_level}，需要加强执行力度"
        else:
            return f"目标'{goal.name}'达成概率{success_level}，建议重新评估目标或策略"
    
    def _assess_risk_level(self, prediction: Prediction, goal: Goal) -> str:
        """评估风险级别"""
        risk_factors = 0
        
        if prediction.success_probability < 0.4:
            risk_factors += 2
        elif prediction.success_probability < 0.6:
            risk_factors += 1
        
        if goal.deadline and (goal.deadline - datetime.now()).days <= 7:
            risk_factors += 2
        elif goal.deadline and (goal.deadline - datetime.now()).days <= 30:
            risk_factors += 1
        
        if prediction.confidence < 0.5:
            risk_factors += 1
        
        if risk_factors >= 4:
            return "高"
        elif risk_factors >= 2:
            return "中"
        else:
            return "低"
    
    def _generate_weekly_recommendations(self, daily_predictions: Dict[str, float]) -> List[str]:
        """生成周度建议"""
        if not daily_predictions:
            return ["建议：开始记录每日状态和活动"]
        
        recommendations = []
        avg_productivity = sum(daily_predictions.values()) / len(daily_predictions)
        
        if avg_productivity < 5:
            recommendations.append("整体生产力偏低，建议重新审视目标和方法")
        elif avg_productivity > 7:
            recommendations.append("生产力水平良好，可以考虑设置更有挑战性的目标")
        
        # 找出最高和最低生产力的日子
        max_day = max(daily_predictions, key=daily_predictions.get)
        min_day = min(daily_predictions, key=daily_predictions.get)
        
        recommendations.append(f"建议在{max_day}安排重要任务，在{min_day}安排轻松活动")
        
        return recommendations
    
    def _calculate_data_freshness(self, states: List[DailyState], 
                                activities: List[DailyActivity]) -> float:
        """计算数据新鲜度"""
        if not states and not activities:
            return 0.0
        
        latest_date = datetime.now().date()
        
        if states:
            latest_state_date = max(s.date for s in states)
            days_since_state = (latest_date - latest_state_date).days
        else:
            days_since_state = 30
        
        if activities:
            latest_activity_date = max(a.date for a in activities if a.date)
            days_since_activity = (latest_date - latest_activity_date).days
        else:
            days_since_activity = 30
        
        avg_days_since = (days_since_state + days_since_activity) / 2
        return max(0.0, 1.0 - avg_days_since / 7.0)
    
    def _calculate_data_completeness(self, states: List[DailyState], 
                                   activities: List[DailyActivity]) -> float:
        """计算数据完整性"""
        expected_days = 30
        
        state_days = len(set(s.date for s in states)) if states else 0
        activity_days = len(set(a.date for a in activities if a.date)) if activities else 0
        
        state_completeness = min(state_days / expected_days, 1.0)
        activity_completeness = min(activity_days / expected_days, 1.0)
        
        return (state_completeness + activity_completeness) / 2
    
    def _generate_data_quality_recommendations(self, states: List[DailyState], 
                                             activities: List[DailyActivity]) -> List[str]:
        """生成数据质量建议"""
        recommendations = []
        
        if len(states) < 14:
            recommendations.append("建议：增加每日状态记录，至少记录14天")
        
        if len(activities) < 21:
            recommendations.append("建议：增加活动记录频率，每天至少记录1-2个活动")
        
        freshness = self._calculate_data_freshness(states, activities)
        if freshness < 0.5:
            recommendations.append("建议：保持数据更新，最好每天都有记录")
        
        completeness = self._calculate_data_completeness(states, activities)
        if completeness < 0.5:
            recommendations.append("建议：提高记录的一致性，避免长时间中断")
        
        return recommendations
    
    # 模式分析相关方法
    def _analyze_activity_frequency(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析活动频率"""
        if not activities:
            return {"message": "无活动数据"}
        
        # 按日期统计
        daily_counts = {}
        for activity in activities:
            if activity.date:
                date_str = activity.date.strftime('%Y-%m-%d')
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        
        if daily_counts:
            avg_daily = sum(daily_counts.values()) / len(daily_counts)
            max_daily = max(daily_counts.values())
            min_daily = min(daily_counts.values())
            
            return {
                "average_daily_activities": avg_daily,
                "max_daily_activities": max_daily,
                "min_daily_activities": min_daily,
                "active_days": len(daily_counts),
                "consistency": len(daily_counts) / 30.0  # 假设30天周期
            }
        
        return {"message": "数据不足"}
    
    def _analyze_efficiency_trends(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析效率趋势"""
        if len(activities) < 7:
            return {"message": "数据不足"}
        
        # 按时间排序
        sorted_activities = sorted([a for a in activities if a.date], key=lambda a: a.date)
        
        # 计算移动平均
        window_size = 7
        trends = []
        
        for i in range(len(sorted_activities) - window_size + 1):
            window = sorted_activities[i:i + window_size]
            avg_efficiency = sum(a.efficiency for a in window) / len(window)
            trends.append(avg_efficiency)
        
        if len(trends) >= 2:
            recent_trend = trends[-1]
            previous_trend = trends[0]
            change = recent_trend - previous_trend
            
            trend_direction = "上升" if change > 0.5 else "下降" if change < -0.5 else "稳定"
            
            return {
                "trend_direction": trend_direction,
                "change_magnitude": abs(change),
                "recent_efficiency": recent_trend,
                "initial_efficiency": previous_trend,
                "overall_average": sum(a.efficiency for a in sorted_activities) / len(sorted_activities)
            }
        
        return {"message": "趋势数据不足"}
    
    def _analyze_state_correlations(self, activities: List[DailyActivity], 
                                  states: List[DailyState]) -> Dict[str, Any]:
        """分析状态与活动的关联"""
        if not activities or not states:
            return {"message": "数据不足"}
        
        # 创建日期到状态的映射
        state_by_date = {s.date: s for s in states}
        
        correlations = {}
        state_metrics = ['mood', 'energy', 'stress', 'focus', 'motivation']
        
        for metric in state_metrics:
            metric_values = []
            efficiency_values = []
            
            for activity in activities:
                if activity.date in state_by_date:
                    state = state_by_date[activity.date]
                    metric_values.append(getattr(state, metric))
                    efficiency_values.append(activity.efficiency)
            
            if len(metric_values) >= 5:  # 至少5个数据点
                # 简单的相关性计算
                correlation = self._calculate_correlation(metric_values, efficiency_values)
                correlations[metric] = correlation
        
        # 找出最强的正相关和负相关
        if correlations:
            strongest_positive = max(correlations.items(), key=lambda x: x[1] if x[1] > 0 else -1)
            strongest_negative = min(correlations.items(), key=lambda x: x[1] if x[1] < 0 else 1)
            
            return {
                "correlations": correlations,
                "strongest_positive_factor": strongest_positive[0] if strongest_positive[1] > 0.3 else None,
                "strongest_negative_factor": strongest_negative[0] if strongest_negative[1] < -0.3 else None,
                "insights": self._generate_correlation_insights(correlations)
            }
        
        return {"message": "无法计算相关性"}
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算简单相关系数"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _generate_correlation_insights(self, correlations: Dict[str, float]) -> List[str]:
        """生成相关性洞察"""
        insights = []
        
        for factor, correlation in correlations.items():
            if correlation > 0.5:
                insights.append(f"{factor}与执行效率呈强正相关，提升{factor}有助于提高表现")
            elif correlation < -0.5:
                insights.append(f"{factor}与执行效率呈强负相关，需要控制{factor}水平")
            elif 0.3 <= correlation <= 0.5:
                insights.append(f"{factor}与执行效率呈中等正相关")
            elif -0.5 <= correlation <= -0.3:
                insights.append(f"{factor}与执行效率呈中等负相关")
        
        return insights
    
    def _identify_optimal_conditions(self, activities: List[DailyActivity], 
                                   states: List[DailyState]) -> Dict[str, Any]:
        """识别最佳执行条件"""
        if not activities or not states:
            return {"message": "数据不足"}
        
        # 找出高效率的活动
        high_efficiency_activities = [a for a in activities if a.efficiency >= 8]
        
        if not high_efficiency_activities:
            return {"message": "暂无高效率活动记录"}
        
        # 分析高效率活动对应的状态
        state_by_date = {s.date: s for s in states}
        optimal_states = []
        
        for activity in high_efficiency_activities:
            if activity.date in state_by_date:
                optimal_states.append(state_by_date[activity.date])
        
        if optimal_states:
            optimal_conditions = {
                "optimal_mood": sum(s.mood for s in optimal_states) / len(optimal_states),
                "optimal_energy": sum(s.energy for s in optimal_states) / len(optimal_states),
                "optimal_stress": sum(s.stress for s in optimal_states) / len(optimal_states),
                "optimal_focus": sum(s.focus for s in optimal_states) / len(optimal_states),
                "optimal_motivation": sum(s.motivation for s in optimal_states) / len(optimal_states),
                "sample_size": len(optimal_states)
            }
            
            return optimal_conditions
        
        return {"message": "无法确定最佳条件"}
    
    def _identify_improvement_opportunities(self, activities: List[DailyActivity], 
                                          states: List[DailyState]) -> List[str]:
        """识别改进机会"""
        opportunities = []
        
        if not activities:
            return ["开始记录日常活动"]
        
        # 分析低效率活动
        low_efficiency_activities = [a for a in activities if a.efficiency <= 4]
        if len(low_efficiency_activities) > len(activities) * 0.3:
            opportunities.append("超过30%的活动效率较低，需要分析原因并改进")
        
        # 分析一致性
        if activities:
            unique_dates = len(set(a.date for a in activities if a.date))
            if unique_dates < len(activities) * 0.5:
                opportunities.append("活动记录不够一致，建议建立每日记录习惯")
        
        # 分析持续时间
        if activities:
            avg_duration = sum(a.duration_minutes for a in activities) / len(activities)
            if avg_duration < 30:
                opportunities.append("活动持续时间较短，可能需要更专注的执行")
            elif avg_duration > 180:
                opportunities.append("活动持续时间较长，考虑分解为更小的任务")
        
        return opportunities
    
    # 系统级分析方法
    def _get_system_overview(self) -> Dict[str, Any]:
        """获取系统概览"""
        summary = self.db.get_data_summary()
        
        return {
            "active_goals": summary['active_goals'],
            "total_records": {
                "states": summary['state_records'],
                "activities": summary['activity_records'],
                "predictions": summary['prediction_records']
            },
            "recent_averages": summary['recent_averages'],
            "system_health": self._calculate_system_health(summary)
        }
    
    def _calculate_system_health(self, summary: Dict[str, Any]) -> str:
        """计算系统健康度"""
        health_score = 0
        
        if summary['active_goals'] > 0:
            health_score += 25
        if summary['state_records'] >= 30:
            health_score += 25
        if summary['activity_records'] >= 50:
            health_score += 25
        if summary['prediction_records'] >= 10:
            health_score += 25
        
        if health_score >= 75:
            return "优秀"
        elif health_score >= 50:
            return "良好"
        elif health_score >= 25:
            return "一般"
        else:
            return "需改进"
    
    def _analyze_global_patterns(self) -> Dict[str, Any]:
        """分析全局模式"""
        # 获取所有活动数据
        all_activities = []
        active_goals = self.db.get_active_goals()
        
        for goal in active_goals:
            activities = self.db.get_goal_activities(goal.id, 60)
            all_activities.extend(activities)
        
        if not all_activities:
            return {"message": "暂无活动数据"}
        
        return {
            "most_productive_weekday": self._find_most_productive_weekday(all_activities),
            "optimal_activity_duration": self._find_optimal_duration(all_activities),
            "activity_type_performance": self._analyze_activity_type_performance(all_activities),
            "seasonal_patterns": self._analyze_seasonal_patterns(all_activities)
        }
    
    def _find_most_productive_weekday(self, activities: List[DailyActivity]) -> str:
        """找出最高效的工作日"""
        weekday_efficiency = {}
        
        for activity in activities:
            if activity.date:
                weekday = activity.date.weekday()
                if weekday not in weekday_efficiency:
                    weekday_efficiency[weekday] = []
                weekday_efficiency[weekday].append(activity.efficiency)
        
        if weekday_efficiency:
            weekday_avg = {day: sum(effs) / len(effs) for day, effs in weekday_efficiency.items()}
            best_day = max(weekday_avg, key=weekday_avg.get)
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            return weekday_names[best_day]
        
        return "数据不足"
    
    def _find_optimal_duration(self, activities: List[DailyActivity]) -> str:
        """找出最佳活动持续时间"""
        duration_efficiency = {}
        
        for activity in activities:
            duration_range = self._get_duration_range(activity.duration_minutes)
            if duration_range not in duration_efficiency:
                duration_efficiency[duration_range] = []
            duration_efficiency[duration_range].append(activity.efficiency)
        
        if duration_efficiency:
            duration_avg = {dur: sum(effs) / len(effs) for dur, effs in duration_efficiency.items()}
            best_duration = max(duration_avg, key=duration_avg.get)
            return best_duration
        
        return "数据不足"
    
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
    
    def _analyze_activity_type_performance(self, activities: List[DailyActivity]) -> Dict[str, float]:
        """分析不同活动类型的表现"""
        type_efficiency = {}
        
        for activity in activities:
            activity_type = activity.activity_type.value
            if activity_type not in type_efficiency:
                type_efficiency[activity_type] = []
            type_efficiency[activity_type].append(activity.efficiency)
        
        return {atype: sum(effs) / len(effs) for atype, effs in type_efficiency.items()}
    
    def _analyze_seasonal_patterns(self, activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析季节性模式"""
        if len(activities) < 30:
            return {"message": "数据不足"}
        
        monthly_efficiency = {}
        for activity in activities:
            if activity.date:
                month = activity.date.month
                if month not in monthly_efficiency:
                    monthly_efficiency[month] = []
                monthly_efficiency[month].append(activity.efficiency)
        
        if len(monthly_efficiency) >= 2:
            monthly_avg = {month: sum(effs) / len(effs) for month, effs in monthly_efficiency.items()}
            best_month = max(monthly_avg, key=monthly_avg.get)
            worst_month = min(monthly_avg, key=monthly_avg.get)
            
            month_names = ["", "1月", "2月", "3月", "4月", "5月", "6月",
                          "7月", "8月", "9月", "10月", "11月", "12月"]
            
            return {
                "best_month": month_names[best_month],
                "worst_month": month_names[worst_month],
                "monthly_averages": monthly_avg
            }
        
        return {"message": "季节性数据不足"}
    
    def _generate_global_recommendations(self) -> List[str]:
        """生成全局建议"""
        recommendations = []
        
        active_goals = self.db.get_active_goals()
        recent_states = self.db.get_recent_states(7)
        
        # 基于目标数量
        if len(active_goals) == 0:
            recommendations.append("建议：设置第一个目标，开始你的改变之旅")
        elif len(active_goals) > 5:
            recommendations.append("建议：目标较多，建议专注于2-3个最重要的目标")
        
        # 基于最近状态
        if recent_states:
            avg_mood = sum(s.mood for s in recent_states) / len(recent_states)
            avg_energy = sum(s.energy for s in recent_states) / len(recent_states)
            avg_stress = sum(s.stress for s in recent_states) / len(recent_states)
            
            if avg_mood < 5:
                recommendations.append("建议：最近心情偏低，尝试增加愉快的活动")
            if avg_energy < 5:
                recommendations.append("建议：精力不足，注意休息和营养补充")
            if avg_stress > 7:
                recommendations.append("建议：压力较大，学习压力管理技巧")
        
        # 基于数据质量
        summary = self.db.get_data_summary()
        if summary['state_records'] < 14:
            recommendations.append("建议：增加每日状态记录，有助于更准确的预测")
        if summary['activity_records'] < 30:
            recommendations.append("建议：增加活动记录，建立完整的行为档案")
        
        return recommendations
    
    def _assess_system_data_health(self) -> Dict[str, Any]:
        """评估系统数据健康度"""
        summary = self.db.get_data_summary()
        recent_states = self.db.get_recent_states(7)
        
        health = {
            "overall_score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        # 数据量评估
        if summary['state_records'] >= 30:
            health["overall_score"] += 25
            health["strengths"].append("状态记录充足")
        else:
            health["weaknesses"].append("状态记录不足")
            health["recommendations"].append("增加每日状态记录")
        
        if summary['activity_records'] >= 50:
            health["overall_score"] += 25
            health["strengths"].append("活动记录丰富")
        else:
            health["weaknesses"].append("活动记录较少")
            health["recommendations"].append("增加活动记录频率")
        
        # 数据新鲜度评估
        if len(recent_states) >= 5:
            health["overall_score"] += 25
            health["strengths"].append("数据更新及时")
        else:
            health["weaknesses"].append("最近数据更新不及时")
            health["recommendations"].append("保持每日记录习惯")
        
        # 目标设定评估
        if summary['active_goals'] > 0:
            health["overall_score"] += 25
            health["strengths"].append("有明确的目标")
        else:
            health["weaknesses"].append("缺少明确目标")
            health["recommendations"].append("设置具体的目标")
        
        # 确定健康等级
        if health["overall_score"] >= 75:
            health["level"] = "优秀"
        elif health["overall_score"] >= 50:
            health["level"] = "良好"
        elif health["overall_score"] >= 25:
            health["level"] = "一般"
        else:
            health["level"] = "需改进"
        
        return health
    
    def _get_goal_status(self, goal: Goal, prediction: Optional[Prediction]) -> str:
        """获取目标状态"""
        completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
        
        if completion_rate >= 1.0:
            return "已完成"
        elif not prediction:
            return "待预测"
        elif prediction.success_probability >= 0.7:
            return "进展良好"
        elif prediction.success_probability >= 0.4:
            return "需要努力"
        else:
            return "面临挑战"
    
    def _get_goal_key_insights(self, goal: Goal, prediction: Optional[Prediction]) -> List[str]:
        """获取目标关键洞察"""
        insights = []
        
        completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
        insights.append(f"当前完成度：{completion_rate:.1%}")
        
        if prediction:
            insights.append(f"成功概率：{prediction.success_probability:.1%}")
            insights.append(f"生产力评分：{prediction.productivity_score:.1f}/10")
            
            # 添加关键因素
            if prediction.key_factors:
                top_factor = max(prediction.key_factors.items(), key=lambda x: x[1])
                insights.append(f"关键因素：{top_factor[0]}")
        
        if goal.deadline:
            days_left = (goal.deadline - datetime.now()).days
            if days_left <= 7:
                insights.append(f"紧急：还有{days_left}天到期")
            elif days_left <= 30:
                insights.append(f"时间：还有{days_left}天")
        
        return insights