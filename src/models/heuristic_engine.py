"""
启发式规则引擎
在数据不足时使用经验规则进行预测
"""
import math
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from ..database.models import Goal, DailyState, DailyActivity, Prediction, GoalCategory, ActivityType
from ..database.database import DatabaseManager


@dataclass
class HeuristicWeights:
    """启发式权重配置"""
    mood_weight: float = 0.15
    energy_weight: float = 0.20
    stress_weight: float = -0.15  # 负权重，压力越高成功率越低
    sleep_weight: float = 0.10
    focus_weight: float = 0.20
    motivation_weight: float = 0.25
    consistency_weight: float = 0.15
    progress_weight: float = 0.30


class HeuristicEngine:
    """启发式预测引擎"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.weights = HeuristicWeights()
        
        # 不同目标类别的基础成功率
        self.base_success_rates = {
            GoalCategory.LEARNING: 0.65,
            GoalCategory.FITNESS: 0.60,
            GoalCategory.WORK: 0.70,
            GoalCategory.PERSONAL: 0.55,
            GoalCategory.HEALTH: 0.65,
            GoalCategory.RELATIONSHIP: 0.50,
            GoalCategory.FINANCE: 0.60,
            GoalCategory.HOBBY: 0.70
        }
    
    def predict_goal_success(self, goal: Goal, target_date: datetime = None) -> Prediction:
        """预测目标成功概率"""
        if target_date is None:
            target_date = goal.deadline or datetime.now() + timedelta(days=30)
        
        # 获取历史数据
        recent_states = self.db.get_recent_states(30)
        goal_activities = self.db.get_goal_activities(goal.id, 30)
        
        # 计算各项指标
        state_score = self._calculate_state_score(recent_states)
        progress_score = self._calculate_progress_score(goal, goal_activities)
        consistency_score = self._calculate_consistency_score(goal_activities)
        time_pressure_score = self._calculate_time_pressure_score(goal, target_date)
        
        # 基础成功率
        base_rate = self.base_success_rates.get(goal.category, 0.60)
        
        # 综合计算成功概率
        success_probability = self._calculate_weighted_probability(
            base_rate, state_score, progress_score, 
            consistency_score, time_pressure_score
        )
        
        # 计算生产力评分
        productivity_score = self._calculate_productivity_score(
            recent_states, goal_activities
        )
        
        # 识别关键影响因素
        key_factors = self._identify_key_factors(
            recent_states, goal_activities, goal
        )
        
        # 生成改进建议
        recommendations = self._generate_recommendations(
            recent_states, goal_activities, goal, key_factors
        )
        
        # 计算置信度
        confidence = self._calculate_confidence(recent_states, goal_activities)
        
        return Prediction(
            goal_id=goal.id,
            prediction_date=datetime.now(),
            target_date=target_date,
            success_probability=max(0.0, min(1.0, success_probability)),
            productivity_score=max(0.0, min(10.0, productivity_score)),
            key_factors=key_factors,
            recommendations=recommendations,
            model_type="heuristic",
            confidence=confidence
        )
    
    def _calculate_state_score(self, states: List[DailyState]) -> float:
        """计算状态评分"""
        if not states:
            return 5.0  # 默认中等水平
        
        # 计算最近状态的加权平均
        total_weight = 0
        weighted_sum = 0
        
        for i, state in enumerate(states[:14]):  # 最近14天
            # 越近的日期权重越高
            weight = 1.0 / (i + 1)
            total_weight += weight
            
            # 计算该天的综合状态评分
            day_score = (
                state.mood * self.weights.mood_weight +
                state.energy * self.weights.energy_weight +
                (10 - state.stress) * abs(self.weights.stress_weight) +  # 转换压力为正向指标
                min(state.sleep_hours / 8 * 10, 10) * self.weights.sleep_weight +
                state.focus * self.weights.focus_weight +
                state.motivation * self.weights.motivation_weight
            )
            
            weighted_sum += day_score * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 5.0
    
    def _calculate_progress_score(self, goal: Goal, activities: List[DailyActivity]) -> float:
        """计算进度评分"""
        if goal.target_value <= 0:
            return 5.0
        
        # 当前完成度
        completion_rate = goal.current_value / goal.target_value
        
        # 基于活动的进度趋势
        if activities:
            recent_progress = sum(act.progress for act in activities[:7]) / len(activities[:7])
            trend_score = recent_progress / 10.0  # 转换为0-1范围
        else:
            trend_score = 0.5
        
        # 综合评分
        progress_score = (completion_rate * 0.6 + trend_score * 0.4) * 10
        return min(progress_score, 10.0)
    
    def _calculate_consistency_score(self, activities: List[DailyActivity]) -> float:
        """计算一致性评分"""
        if len(activities) < 7:
            return 3.0  # 数据不足，给较低分
        
        # 计算最近30天的活动频率
        activity_days = set()
        for activity in activities:
            if activity.date:
                activity_days.add(activity.date)
        
        # 一致性 = 活动天数 / 总天数
        total_days = min(30, len(activities))
        consistency = len(activity_days) / total_days if total_days > 0 else 0
        
        return consistency * 10
    
    def _calculate_time_pressure_score(self, goal: Goal, target_date: datetime) -> float:
        """计算时间压力评分"""
        if not goal.deadline:
            return 7.0  # 无截止日期，压力适中
        
        days_left = (goal.deadline - datetime.now()).days
        
        if days_left <= 0:
            return 2.0  # 已过期
        elif days_left <= 7:
            return 4.0  # 高压力
        elif days_left <= 30:
            return 6.0  # 中等压力
        else:
            return 8.0  # 低压力
    
    def _calculate_weighted_probability(self, base_rate: float, state_score: float,
                                      progress_score: float, consistency_score: float,
                                      time_pressure_score: float) -> float:
        """计算加权成功概率"""
        # 将各项评分标准化到0-1范围
        normalized_state = state_score / 10.0
        normalized_progress = progress_score / 10.0
        normalized_consistency = consistency_score / 10.0
        normalized_time = time_pressure_score / 10.0
        
        # 加权计算
        weighted_score = (
            normalized_state * 0.25 +
            normalized_progress * 0.35 +
            normalized_consistency * 0.25 +
            normalized_time * 0.15
        )
        
        # 与基础成功率结合
        final_probability = base_rate * 0.4 + weighted_score * 0.6
        
        return final_probability
    
    def _calculate_productivity_score(self, states: List[DailyState], 
                                    activities: List[DailyActivity]) -> float:
        """计算生产力评分"""
        if not states and not activities:
            return 5.0
        
        # 状态贡献
        state_contribution = 0
        if states:
            avg_energy = sum(s.energy for s in states[:7]) / len(states[:7])
            avg_focus = sum(s.focus for s in states[:7]) / len(states[:7])
            avg_motivation = sum(s.motivation for s in states[:7]) / len(states[:7])
            state_contribution = (avg_energy + avg_focus + avg_motivation) / 3
        
        # 活动效率贡献
        activity_contribution = 0
        if activities:
            avg_efficiency = sum(a.efficiency for a in activities[:14]) / len(activities[:14])
            avg_satisfaction = sum(a.satisfaction for a in activities[:14]) / len(activities[:14])
            activity_contribution = (avg_efficiency + avg_satisfaction) / 2
        
        # 综合评分
        if states and activities:
            return (state_contribution + activity_contribution) / 2
        elif states:
            return state_contribution
        else:
            return activity_contribution
    
    def _identify_key_factors(self, states: List[DailyState], 
                            activities: List[DailyActivity], goal: Goal) -> Dict[str, float]:
        """识别关键影响因素"""
        factors = {}
        
        if states:
            recent_states = states[:7]
            avg_mood = sum(s.mood for s in recent_states) / len(recent_states)
            avg_energy = sum(s.energy for s in recent_states) / len(recent_states)
            avg_stress = sum(s.stress for s in recent_states) / len(recent_states)
            avg_sleep = sum(s.sleep_hours for s in recent_states) / len(recent_states)
            avg_focus = sum(s.focus for s in recent_states) / len(recent_states)
            avg_motivation = sum(s.motivation for s in recent_states) / len(recent_states)
            
            factors.update({
                "心情状态": avg_mood / 10.0,
                "精力水平": avg_energy / 10.0,
                "压力水平": (10 - avg_stress) / 10.0,  # 转换为正向指标
                "睡眠质量": min(avg_sleep / 8, 1.0),
                "专注度": avg_focus / 10.0,
                "动机水平": avg_motivation / 10.0
            })
        
        if activities:
            recent_activities = activities[:14]
            avg_efficiency = sum(a.efficiency for a in recent_activities) / len(recent_activities)
            avg_progress = sum(a.progress for a in recent_activities) / len(recent_activities)
            
            # 计算活动一致性
            activity_days = len(set(a.date for a in recent_activities if a.date))
            consistency = activity_days / 14.0
            
            factors.update({
                "执行效率": avg_efficiency / 10.0,
                "进度完成": avg_progress / 100.0,
                "行动一致性": consistency
            })
        
        # 目标相关因素
        if goal.deadline:
            days_left = (goal.deadline - datetime.now()).days
            time_factor = max(0, min(1, days_left / 30))  # 30天内的时间压力
            factors["时间充裕度"] = time_factor
        
        if goal.target_value > 0:
            completion = goal.current_value / goal.target_value
            factors["目标完成度"] = min(completion, 1.0)
        
        return factors
    
    def _generate_recommendations(self, states: List[DailyState], 
                                activities: List[DailyActivity], goal: Goal,
                                key_factors: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于关键因素生成建议
        for factor, score in key_factors.items():
            if score < 0.6:  # 低于60%需要改进
                if factor == "心情状态":
                    recommendations.append("建议：通过运动、音乐或社交活动来改善心情状态")
                elif factor == "精力水平":
                    recommendations.append("建议：优化作息时间，确保充足休息，适当补充营养")
                elif factor == "压力水平":
                    recommendations.append("建议：学习压力管理技巧，如冥想、深呼吸或时间管理")
                elif factor == "睡眠质量":
                    recommendations.append("建议：建立规律的睡眠习惯，每晚保证7-8小时优质睡眠")
                elif factor == "专注度":
                    recommendations.append("建议：创造专注的工作环境，使用番茄工作法等专注技巧")
                elif factor == "动机水平":
                    recommendations.append("建议：重新审视目标意义，设置小的里程碑来保持动机")
                elif factor == "执行效率":
                    recommendations.append("建议：分析低效原因，优化工作流程和方法")
                elif factor == "行动一致性":
                    recommendations.append("建议：制定具体的行动计划，设置提醒来保持一致性")
        
        # 基于目标类别的特定建议
        if goal.category == GoalCategory.LEARNING:
            if not any("学习" in r for r in recommendations):
                recommendations.append("学习建议：采用主动学习法，定期复习和实践")
        elif goal.category == GoalCategory.FITNESS:
            if not any("运动" in r for r in recommendations):
                recommendations.append("健身建议：循序渐进，注意休息恢复，保持运动多样性")
        elif goal.category == GoalCategory.WORK:
            if not any("工作" in r for r in recommendations):
                recommendations.append("工作建议：优先处理重要任务，合理分配时间和精力")
        
        # 基于时间压力的建议
        if goal.deadline:
            days_left = (goal.deadline - datetime.now()).days
            if days_left <= 7:
                recommendations.append("紧急提醒：目标截止日期临近，建议集中精力完成核心任务")
            elif days_left <= 30:
                recommendations.append("时间提醒：合理规划剩余时间，避免最后阶段的时间压力")
        
        # 确保至少有一条建议
        if not recommendations:
            recommendations.append("建议：保持当前良好状态，继续坚持既定计划")
        
        return recommendations[:5]  # 最多返回5条建议
    
    def _calculate_confidence(self, states: List[DailyState], 
                            activities: List[DailyActivity]) -> float:
        """计算预测置信度"""
        # 基于数据量和质量计算置信度
        state_data_score = min(len(states) / 14.0, 1.0)  # 14天数据为满分
        activity_data_score = min(len(activities) / 21.0, 1.0)  # 21次活动为满分
        
        # 数据新鲜度
        freshness_score = 1.0
        if states:
            latest_state = max(states, key=lambda s: s.date)
            days_since_latest = (date.today() - latest_state.date).days
            freshness_score = max(0.5, 1.0 - days_since_latest / 7.0)
        
        # 综合置信度
        confidence = (state_data_score * 0.4 + activity_data_score * 0.4 + 
                     freshness_score * 0.2)
        
        return confidence
    
    def predict_weekly_productivity(self, target_date: datetime = None) -> Dict[str, float]:
        """预测未来一周的生产力水平"""
        if target_date is None:
            target_date = datetime.now() + timedelta(days=7)
        
        recent_states = self.db.get_recent_states(14)
        recent_activities = []
        
        # 获取所有目标的最近活动
        active_goals = self.db.get_active_goals()
        for goal in active_goals:
            goal_activities = self.db.get_goal_activities(goal.id, 14)
            recent_activities.extend(goal_activities)
        
        # 计算基础生产力趋势
        base_productivity = self._calculate_productivity_score(recent_states, recent_activities)
        
        # 预测每天的生产力变化
        daily_predictions = {}
        for i in range(7):
            day = target_date + timedelta(days=i)
            
            # 基于历史模式调整（周末通常生产力较低）
            weekday_factor = 0.8 if day.weekday() >= 5 else 1.0
            
            # 基于趋势调整
            trend_factor = 1.0 + (i * 0.02)  # 假设轻微上升趋势
            
            daily_productivity = base_productivity * weekday_factor * trend_factor
            daily_predictions[day.strftime('%Y-%m-%d')] = min(daily_productivity, 10.0)
        
        return daily_predictions