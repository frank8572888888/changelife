"""
机器学习预测模型
使用随机森林等算法进行目标成功率预测
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

from ..database.models import Goal, DailyState, DailyActivity, Prediction, ModelMetrics, GoalCategory
from ..database.database import DatabaseManager


class MLPredictor:
    """机器学习预测器"""
    
    def __init__(self, db_manager: DatabaseManager, model_dir: str = "models"):
        self.db = db_manager
        self.model_dir = model_dir
        self._ensure_model_directory()
        
        # 模型组件
        self.success_model = None
        self.productivity_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # 模型参数
        self.min_samples_for_training = 30
        self.feature_names = []
        
        # 尝试加载已有模型
        self._load_models()
    
    def _ensure_model_directory(self):
        """确保模型目录存在"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def _load_models(self):
        """加载已保存的模型"""
        try:
            success_model_path = os.path.join(self.model_dir, "success_model.joblib")
            productivity_model_path = os.path.join(self.model_dir, "productivity_model.joblib")
            scaler_path = os.path.join(self.model_dir, "scaler.joblib")
            encoders_path = os.path.join(self.model_dir, "encoders.joblib")
            
            if all(os.path.exists(p) for p in [success_model_path, productivity_model_path, scaler_path]):
                self.success_model = joblib.load(success_model_path)
                self.productivity_model = joblib.load(productivity_model_path)
                self.scaler = joblib.load(scaler_path)
                
                if os.path.exists(encoders_path):
                    self.label_encoders = joblib.load(encoders_path)
                
                print("已加载预训练模型")
        except Exception as e:
            print(f"加载模型失败: {e}")
            self.success_model = None
            self.productivity_model = None
    
    def _save_models(self):
        """保存训练好的模型"""
        try:
            joblib.dump(self.success_model, os.path.join(self.model_dir, "success_model.joblib"))
            joblib.dump(self.productivity_model, os.path.join(self.model_dir, "productivity_model.joblib"))
            joblib.dump(self.scaler, os.path.join(self.model_dir, "scaler.joblib"))
            joblib.dump(self.label_encoders, os.path.join(self.model_dir, "encoders.joblib"))
            print("模型已保存")
        except Exception as e:
            print(f"保存模型失败: {e}")
    
    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """准备训练数据"""
        # 获取所有历史数据
        goals = self.db.get_active_goals()
        all_states = self.db.get_recent_states(365)  # 最近一年的数据
        
        training_data = []
        success_labels = []
        productivity_labels = []
        
        for goal in goals:
            goal_activities = self.db.get_goal_activities(goal.id, 365)
            
            if len(goal_activities) < 5:  # 数据太少跳过
                continue
            
            # 为每个时间窗口创建训练样本
            for i in range(7, len(goal_activities)):  # 使用前7天预测后续表现
                # 特征：前7天的状态和活动数据
                window_activities = goal_activities[i-7:i]
                window_dates = [act.date for act in window_activities if act.date]
                
                if not window_dates:
                    continue
                
                # 获取对应时间段的状态数据
                window_states = [s for s in all_states 
                               if s.date in window_dates]
                
                if len(window_states) < 3:  # 状态数据太少跳过
                    continue
                
                # 提取特征
                features = self._extract_features(window_states, window_activities, goal)
                
                # 标签：后续7天的表现
                future_activities = goal_activities[i:i+7] if i+7 <= len(goal_activities) else goal_activities[i:]
                
                if future_activities:
                    # 成功标签：平均效率和进度
                    avg_efficiency = np.mean([act.efficiency for act in future_activities])
                    avg_progress = np.mean([act.progress for act in future_activities])
                    success_score = (avg_efficiency + avg_progress/10) / 2  # 标准化到0-10
                    
                    success_labels.append(1 if success_score >= 6 else 0)  # 二分类
                    productivity_labels.append(success_score)
                    training_data.append(features)
        
        if len(training_data) < self.min_samples_for_training:
            raise ValueError(f"训练数据不足，需要至少{self.min_samples_for_training}个样本，当前只有{len(training_data)}个")
        
        df = pd.DataFrame(training_data)
        self.feature_names = df.columns.tolist()
        
        return df, pd.Series(success_labels), pd.Series(productivity_labels)
    
    def _extract_features(self, states: List[DailyState], 
                         activities: List[DailyActivity], goal: Goal) -> Dict[str, float]:
        """提取特征"""
        features = {}
        
        # 状态特征
        if states:
            features.update({
                'avg_mood': np.mean([s.mood for s in states]),
                'avg_energy': np.mean([s.energy for s in states]),
                'avg_stress': np.mean([s.stress for s in states]),
                'avg_sleep_hours': np.mean([s.sleep_hours for s in states]),
                'avg_sleep_quality': np.mean([s.sleep_quality for s in states]),
                'avg_focus': np.mean([s.focus for s in states]),
                'avg_motivation': np.mean([s.motivation for s in states]),
                'avg_health': np.mean([s.health for s in states]),
                
                # 状态变异性
                'mood_std': np.std([s.mood for s in states]),
                'energy_std': np.std([s.energy for s in states]),
                'stress_std': np.std([s.stress for s in states]),
            })
        else:
            # 默认值
            for key in ['avg_mood', 'avg_energy', 'avg_stress', 'avg_sleep_hours',
                       'avg_sleep_quality', 'avg_focus', 'avg_motivation', 'avg_health',
                       'mood_std', 'energy_std', 'stress_std']:
                features[key] = 5.0
        
        # 活动特征
        if activities:
            features.update({
                'avg_efficiency': np.mean([a.efficiency for a in activities]),
                'avg_progress': np.mean([a.progress for a in activities]),
                'avg_satisfaction': np.mean([a.satisfaction for a in activities]),
                'total_duration': sum([a.duration_minutes for a in activities]),
                'activity_count': len(activities),
                'activity_consistency': len(set(a.date for a in activities if a.date)) / 7.0,
                
                # 活动变异性
                'efficiency_std': np.std([a.efficiency for a in activities]),
                'progress_std': np.std([a.progress for a in activities]),
            })
        else:
            for key in ['avg_efficiency', 'avg_progress', 'avg_satisfaction',
                       'total_duration', 'activity_count', 'activity_consistency',
                       'efficiency_std', 'progress_std']:
                features[key] = 0.0
        
        # 目标特征
        features.update({
            'goal_priority': goal.priority,
            'goal_completion_rate': goal.current_value / goal.target_value if goal.target_value > 0 else 0,
            'goal_category_encoded': self._encode_category(goal.category),
        })
        
        # 时间特征
        if goal.deadline:
            days_to_deadline = (goal.deadline - datetime.now()).days
            features['days_to_deadline'] = max(0, days_to_deadline)
            features['time_pressure'] = 1.0 / (days_to_deadline + 1) if days_to_deadline > 0 else 1.0
        else:
            features['days_to_deadline'] = 365  # 默认一年
            features['time_pressure'] = 0.0
        
        # 周期性特征
        current_date = datetime.now()
        features['day_of_week'] = current_date.weekday()
        features['is_weekend'] = 1.0 if current_date.weekday() >= 5 else 0.0
        features['month'] = current_date.month
        
        return features
    
    def _encode_category(self, category: GoalCategory) -> float:
        """编码目标类别"""
        if 'goal_category' not in self.label_encoders:
            self.label_encoders['goal_category'] = LabelEncoder()
            # 预定义所有可能的类别
            all_categories = [cat.value for cat in GoalCategory]
            self.label_encoders['goal_category'].fit(all_categories)
        
        return float(self.label_encoders['goal_category'].transform([category.value])[0])
    
    def train_models(self) -> Dict[str, float]:
        """训练模型"""
        try:
            # 准备数据
            X, y_success, y_productivity = self.prepare_training_data()
            
            # 数据预处理
            X_scaled = self.scaler.fit_transform(X)
            
            # 分割数据
            X_train, X_test, y_success_train, y_success_test = train_test_split(
                X_scaled, y_success, test_size=0.2, random_state=42
            )
            _, _, y_prod_train, y_prod_test = train_test_split(
                X_scaled, y_productivity, test_size=0.2, random_state=42
            )
            
            # 训练成功率分类模型
            self.success_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            self.success_model.fit(X_train, y_success_train)
            
            # 训练生产力回归模型
            self.productivity_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            self.productivity_model.fit(X_train, y_prod_train)
            
            # 评估模型
            success_pred = self.success_model.predict(X_test)
            prod_pred = self.productivity_model.predict(X_test)
            
            metrics = {
                'success_accuracy': accuracy_score(y_success_test, success_pred),
                'success_precision': precision_score(y_success_test, success_pred, average='weighted'),
                'success_recall': recall_score(y_success_test, success_pred, average='weighted'),
                'success_f1': f1_score(y_success_test, success_pred, average='weighted'),
                'productivity_mse': np.mean((y_prod_test - prod_pred) ** 2),
                'productivity_r2': self.productivity_model.score(X_test, y_prod_test),
                'training_samples': len(X)
            }
            
            # 保存模型
            self._save_models()
            
            # 保存模型指标到数据库
            model_metrics = ModelMetrics(
                model_type="random_forest",
                accuracy=metrics['success_accuracy'],
                precision=metrics['success_precision'],
                recall=metrics['success_recall'],
                f1_score=metrics['success_f1'],
                training_samples=metrics['training_samples'],
                last_trained=datetime.now()
            )
            self.db.save_model_metrics(model_metrics)
            
            print(f"模型训练完成，准确率: {metrics['success_accuracy']:.3f}")
            return metrics
            
        except Exception as e:
            print(f"模型训练失败: {e}")
            return {}
    
    def predict_goal_success(self, goal: Goal, target_date: datetime = None) -> Optional[Prediction]:
        """使用ML模型预测目标成功"""
        if self.success_model is None or self.productivity_model is None:
            return None
        
        try:
            # 获取最近数据
            recent_states = self.db.get_recent_states(7)
            goal_activities = self.db.get_goal_activities(goal.id, 7)
            
            # 提取特征
            features = self._extract_features(recent_states, goal_activities, goal)
            
            # 确保特征顺序一致
            feature_vector = []
            for name in self.feature_names:
                feature_vector.append(features.get(name, 0.0))
            
            # 预处理
            X = np.array(feature_vector).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            # 预测
            success_prob = self.success_model.predict_proba(X_scaled)[0][1]  # 成功的概率
            productivity_score = self.productivity_model.predict(X_scaled)[0]
            
            # 获取特征重要性
            feature_importance = dict(zip(self.feature_names, self.success_model.feature_importances_))
            top_factors = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # 生成建议
            recommendations = self._generate_ml_recommendations(features, top_factors)
            
            # 计算置信度
            confidence = self._calculate_ml_confidence(recent_states, goal_activities)
            
            if target_date is None:
                target_date = goal.deadline or datetime.now() + timedelta(days=30)
            
            return Prediction(
                goal_id=goal.id,
                prediction_date=datetime.now(),
                target_date=target_date,
                success_probability=float(success_prob),
                productivity_score=float(max(0, min(10, productivity_score))),
                key_factors=top_factors,
                recommendations=recommendations,
                model_type="ml",
                confidence=confidence
            )
            
        except Exception as e:
            print(f"ML预测失败: {e}")
            return None
    
    def _generate_ml_recommendations(self, features: Dict[str, float], 
                                   top_factors: Dict[str, float]) -> List[str]:
        """基于ML模型生成建议"""
        recommendations = []
        
        # 基于重要特征生成建议
        for factor, importance in top_factors.items():
            if importance > 0.1:  # 重要性超过10%
                if 'mood' in factor and features.get(factor, 5) < 6:
                    recommendations.append("ML建议：心情状态对成功率影响较大，建议通过积极活动改善心情")
                elif 'energy' in factor and features.get(factor, 5) < 6:
                    recommendations.append("ML建议：精力水平是关键因素，建议优化作息和营养")
                elif 'efficiency' in factor and features.get(factor, 5) < 6:
                    recommendations.append("ML建议：执行效率需要提升，建议优化工作方法和环境")
                elif 'consistency' in factor and features.get(factor, 0.5) < 0.6:
                    recommendations.append("ML建议：行动一致性很重要，建议制定更具体的执行计划")
                elif 'stress' in factor and features.get(factor, 5) > 7:
                    recommendations.append("ML建议：压力水平过高，建议学习压力管理技巧")
        
        # 基于特征值的具体建议
        if features.get('activity_consistency', 0) < 0.5:
            recommendations.append("ML建议：提高行动频率，建立每日执行习惯")
        
        if features.get('time_pressure', 0) > 0.8:
            recommendations.append("ML建议：时间压力较大，建议重新评估目标或调整计划")
        
        return recommendations[:4]  # 最多4条建议
    
    def _calculate_ml_confidence(self, states: List[DailyState], 
                               activities: List[DailyActivity]) -> float:
        """计算ML预测的置信度"""
        # 基于数据质量和模型性能
        data_quality = min(len(states) / 7.0, 1.0) * 0.5 + min(len(activities) / 7.0, 1.0) * 0.5
        
        # 获取最新的模型指标
        latest_metrics = self.db.get_latest_model_metrics("random_forest")
        model_performance = latest_metrics.accuracy if latest_metrics else 0.7
        
        return data_quality * 0.6 + model_performance * 0.4
    
    def should_retrain(self) -> bool:
        """判断是否需要重新训练模型"""
        # 检查是否有足够的新数据
        latest_metrics = self.db.get_latest_model_metrics("random_forest")
        
        if latest_metrics is None:
            return True
        
        # 检查训练时间
        days_since_training = (datetime.now() - latest_metrics.last_trained).days
        if days_since_training > 30:  # 超过30天
            return True
        
        # 检查数据量增长
        current_data_count = len(self.db.get_recent_states(365))
        if current_data_count > latest_metrics.training_samples * 1.5:  # 数据增长50%以上
            return True
        
        return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if self.success_model is None:
            return {}
        
        return dict(zip(self.feature_names, self.success_model.feature_importances_))
    
    def is_model_available(self) -> bool:
        """检查模型是否可用"""
        return self.success_model is not None and self.productivity_model is not None