"""
DeepSeek API客户端
集成外部AI服务获取智能预测和建议
"""
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

from ..database.models import Goal, DailyState, DailyActivity, Prediction, GoalCategory
from ..database.database import DatabaseManager


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        
        if not self.api_key:
            print("警告：未设置DeepSeek API密钥，AI功能将不可用")
    
    def is_available(self) -> bool:
        """检查API是否可用"""
        return bool(self.api_key)
    
    def predict_goal_success(self, goal: Goal, states: List[DailyState], 
                           activities: List[DailyActivity], 
                           target_date: datetime = None) -> Optional[Prediction]:
        """使用AI预测目标成功率"""
        if not self.is_available():
            return None
        
        try:
            # 准备数据摘要
            data_summary = self._prepare_data_summary(goal, states, activities)
            
            # 构建提示词
            prompt = self._build_prediction_prompt(goal, data_summary, target_date)
            
            # 调用API
            response = self._call_api(prompt)
            
            if response:
                return self._parse_prediction_response(response, goal, target_date)
            
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
        
        return None
    
    def get_personalized_recommendations(self, goal: Goal, states: List[DailyState],
                                       activities: List[DailyActivity],
                                       current_prediction: Prediction = None) -> List[str]:
        """获取个性化建议"""
        if not self.is_available():
            return []
        
        try:
            # 准备上下文数据
            context = self._prepare_recommendation_context(goal, states, activities, current_prediction)
            
            # 构建提示词
            prompt = self._build_recommendation_prompt(context)
            
            # 调用API
            response = self._call_api(prompt)
            
            if response:
                return self._parse_recommendations_response(response)
            
        except Exception as e:
            print(f"获取AI建议失败: {e}")
        
        return []
    
    def analyze_patterns(self, goals: List[Goal], states: List[DailyState],
                        activities: List[DailyActivity]) -> Dict[str, Any]:
        """分析行为模式和趋势"""
        if not self.is_available():
            return {}
        
        try:
            # 准备分析数据
            analysis_data = self._prepare_analysis_data(goals, states, activities)
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(analysis_data)
            
            # 调用API
            response = self._call_api(prompt)
            
            if response:
                return self._parse_analysis_response(response)
            
        except Exception as e:
            print(f"模式分析失败: {e}")
        
        return {}
    
    def _prepare_data_summary(self, goal: Goal, states: List[DailyState], 
                            activities: List[DailyActivity]) -> Dict[str, Any]:
        """准备数据摘要"""
        summary = {
            "goal": {
                "name": goal.name,
                "category": goal.category.value,
                "description": goal.description,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "completion_rate": goal.current_value / goal.target_value if goal.target_value > 0 else 0,
                "priority": goal.priority,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
                "days_to_deadline": (goal.deadline - datetime.now()).days if goal.deadline else None
            },
            "recent_states": [],
            "recent_activities": []
        }
        
        # 最近7天的状态摘要
        for state in states[:7]:
            summary["recent_states"].append({
                "date": state.date.isoformat(),
                "mood": state.mood,
                "energy": state.energy,
                "stress": state.stress,
                "sleep_hours": state.sleep_hours,
                "sleep_quality": state.sleep_quality,
                "focus": state.focus,
                "motivation": state.motivation,
                "health": state.health
            })
        
        # 最近活动摘要
        for activity in activities[:14]:
            summary["recent_activities"].append({
                "date": activity.date.isoformat() if activity.date else None,
                "type": activity.activity_type.value,
                "description": activity.description,
                "duration_minutes": activity.duration_minutes,
                "efficiency": activity.efficiency,
                "progress": activity.progress,
                "satisfaction": activity.satisfaction
            })
        
        return summary
    
    def _build_prediction_prompt(self, goal: Goal, data_summary: Dict[str, Any], 
                               target_date: datetime = None) -> str:
        """构建预测提示词"""
        target_str = target_date.strftime("%Y-%m-%d") if target_date else "未来30天"
        
        prompt = f"""
作为一个专业的目标管理和生产力分析师，请基于以下数据预测目标达成情况：

目标信息：
- 目标名称：{goal.name}
- 目标类别：{goal.category.value}
- 目标描述：{goal.description}
- 目标值：{goal.target_value} {goal.unit}
- 当前进度：{goal.current_value} {goal.unit} ({data_summary['goal']['completion_rate']:.1%})
- 优先级：{goal.priority}/5
- 截止日期：{data_summary['goal']['deadline'] or '无'}

最近状态数据：
{json.dumps(data_summary['recent_states'], ensure_ascii=False, indent=2)}

最近活动数据：
{json.dumps(data_summary['recent_activities'], ensure_ascii=False, indent=2)}

请分析并预测到{target_str}的目标达成情况，返回JSON格式结果：
{{
    "success_probability": 0.75,  // 成功概率 (0-1)
    "productivity_score": 7.2,    // 生产力评分 (0-10)
    "confidence": 0.85,           // 预测置信度 (0-1)
    "key_factors": {{             // 关键影响因素及权重
        "动机水平": 0.25,
        "执行一致性": 0.20,
        "时间管理": 0.18
    }},
    "risk_factors": [             // 风险因素
        "睡眠质量不稳定",
        "压力水平偏高"
    ],
    "success_factors": [          // 成功因素
        "目标明确具体",
        "执行效率较高"
    ]
}}

请基于数据进行客观分析，考虑历史趋势、当前状态和目标特性。
"""
        return prompt
    
    def _build_recommendation_prompt(self, context: Dict[str, Any]) -> str:
        """构建建议提示词"""
        prompt = f"""
作为专业的个人发展教练，基于以下用户数据提供个性化的改进建议：

用户情况：
{json.dumps(context, ensure_ascii=False, indent=2)}

请提供3-5条具体、可执行的改进建议，每条建议应该：
1. 针对识别出的关键问题
2. 提供具体的行动步骤
3. 考虑用户的实际情况和限制

返回JSON格式：
{{
    "recommendations": [
        {{
            "category": "睡眠优化",
            "priority": "高",
            "action": "建立固定的睡前例程，每晚10:30开始准备睡觉",
            "reason": "睡眠质量直接影响次日的精力和专注度",
            "expected_impact": "提升20%的日间精力水平"
        }}
    ]
}}
"""
        return prompt
    
    def _build_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        prompt = f"""
作为数据分析专家，请分析用户的行为模式和趋势：

用户数据：
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

请分析并返回JSON格式结果：
{{
    "patterns": {{
        "productivity_peaks": ["周二", "周四"],
        "low_energy_periods": ["周一上午", "周五下午"],
        "optimal_work_duration": 90
    }},
    "trends": {{
        "motivation_trend": "上升",
        "efficiency_trend": "稳定",
        "stress_trend": "下降"
    }},
    "insights": [
        "用户在周中工作效率最高",
        "睡眠时间与次日表现呈正相关"
    ],
    "optimization_opportunities": [
        "可以将重要任务安排在周二和周四",
        "建议在低能量时段安排轻松任务"
    ]
}}
"""
        return prompt
    
    def _call_api(self, prompt: str, model: str = "deepseek-chat") -> Optional[str]:
        """调用DeepSeek API"""
        if not self.api_key:
            return None
        
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"API调用失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"API调用异常: {e}")
            return None
    
    def _parse_prediction_response(self, response: str, goal: Goal, 
                                 target_date: datetime = None) -> Optional[Prediction]:
        """解析预测响应"""
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                if target_date is None:
                    target_date = goal.deadline or datetime.now() + timedelta(days=30)
                
                return Prediction(
                    goal_id=goal.id,
                    prediction_date=datetime.now(),
                    target_date=target_date,
                    success_probability=float(data.get("success_probability", 0.5)),
                    productivity_score=float(data.get("productivity_score", 5.0)),
                    key_factors=data.get("key_factors", {}),
                    recommendations=data.get("risk_factors", []) + data.get("success_factors", []),
                    model_type="ai",
                    confidence=float(data.get("confidence", 0.7))
                )
        except Exception as e:
            print(f"解析预测响应失败: {e}")
        
        return None
    
    def _parse_recommendations_response(self, response: str) -> List[str]:
        """解析建议响应"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                recommendations = []
                for rec in data.get("recommendations", []):
                    rec_text = f"【{rec.get('category', '建议')}】{rec.get('action', '')}"
                    if rec.get('reason'):
                        rec_text += f" - {rec.get('reason')}"
                    recommendations.append(rec_text)
                
                return recommendations
        except Exception as e:
            print(f"解析建议响应失败: {e}")
        
        return []
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析分析响应"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            print(f"解析分析响应失败: {e}")
        
        return {}
    
    def _prepare_recommendation_context(self, goal: Goal, states: List[DailyState],
                                      activities: List[DailyActivity],
                                      prediction: Prediction = None) -> Dict[str, Any]:
        """准备建议上下文"""
        context = {
            "goal_info": {
                "name": goal.name,
                "category": goal.category.value,
                "completion_rate": goal.current_value / goal.target_value if goal.target_value > 0 else 0,
                "priority": goal.priority
            },
            "current_challenges": [],
            "recent_performance": {}
        }
        
        # 识别当前挑战
        if states:
            avg_mood = sum(s.mood for s in states[:7]) / len(states[:7])
            avg_energy = sum(s.energy for s in states[:7]) / len(states[:7])
            avg_stress = sum(s.stress for s in states[:7]) / len(states[:7])
            
            if avg_mood < 6:
                context["current_challenges"].append("心情状态偏低")
            if avg_energy < 6:
                context["current_challenges"].append("精力不足")
            if avg_stress > 7:
                context["current_challenges"].append("压力过大")
        
        # 最近表现
        if activities:
            avg_efficiency = sum(a.efficiency for a in activities[:7]) / len(activities[:7])
            context["recent_performance"]["efficiency"] = avg_efficiency
            context["recent_performance"]["consistency"] = len(set(a.date for a in activities[:7] if a.date)) / 7
        
        # 预测信息
        if prediction:
            context["prediction"] = {
                "success_probability": prediction.success_probability,
                "key_factors": prediction.key_factors
            }
        
        return context
    
    def _prepare_analysis_data(self, goals: List[Goal], states: List[DailyState],
                             activities: List[DailyActivity]) -> Dict[str, Any]:
        """准备分析数据"""
        return {
            "goals_summary": {
                "total_goals": len(goals),
                "categories": [g.category.value for g in goals],
                "avg_completion": sum(g.current_value / g.target_value if g.target_value > 0 else 0 for g in goals) / len(goals) if goals else 0
            },
            "states_trends": {
                "mood_trend": [s.mood for s in states[-14:]] if len(states) >= 14 else [],
                "energy_trend": [s.energy for s in states[-14:]] if len(states) >= 14 else [],
                "stress_trend": [s.stress for s in states[-14:]] if len(states) >= 14 else []
            },
            "activity_patterns": {
                "daily_counts": {},
                "efficiency_by_type": {},
                "duration_patterns": {}
            }
        }


class AIPredictor:
    """AI预测器包装类"""
    
    def __init__(self, db_manager: DatabaseManager, deepseek_client: DeepSeekClient):
        self.db = db_manager
        self.ai_client = deepseek_client
    
    def predict_goal_success(self, goal: Goal, target_date: datetime = None) -> Optional[Prediction]:
        """使用AI预测目标成功"""
        if not self.ai_client.is_available():
            return None
        
        # 获取相关数据
        recent_states = self.db.get_recent_states(14)
        goal_activities = self.db.get_goal_activities(goal.id, 21)
        
        return self.ai_client.predict_goal_success(goal, recent_states, goal_activities, target_date)
    
    def get_enhanced_recommendations(self, goal: Goal, base_prediction: Prediction) -> List[str]:
        """获取增强的AI建议"""
        if not self.ai_client.is_available():
            return base_prediction.recommendations
        
        recent_states = self.db.get_recent_states(14)
        goal_activities = self.db.get_goal_activities(goal.id, 21)
        
        ai_recommendations = self.ai_client.get_personalized_recommendations(
            goal, recent_states, goal_activities, base_prediction
        )
        
        # 合并基础建议和AI建议
        all_recommendations = base_prediction.recommendations + ai_recommendations
        return list(dict.fromkeys(all_recommendations))[:6]  # 去重并限制数量