"""
数据库操作层
提供SQLite数据库的增删改查功能
"""
import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import (
    Goal, DailyState, DailyActivity, Prediction, ModelMetrics,
    GoalCategory, StateType, ActivityType, DATABASE_SCHEMA
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/goals.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            for table_name, schema in DATABASE_SCHEMA.items():
                conn.execute(schema)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    # 目标相关操作
    def create_goal(self, goal: Goal) -> int:
        """创建新目标"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO goals (name, category, description, target_value, 
                                 current_value, unit, deadline, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                goal.name, goal.category.value, goal.description,
                goal.target_value, goal.current_value, goal.unit,
                goal.deadline, goal.priority
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_goal(self, goal_id: int) -> Optional[Goal]:
        """获取单个目标"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM goals WHERE id = ?', (goal_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_goal(row)
            return None
    
    def get_active_goals(self) -> List[Goal]:
        """获取所有活跃目标"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM goals WHERE is_active = 1 ORDER BY priority DESC')
            return [self._row_to_goal(row) for row in cursor.fetchall()]
    
    def update_goal(self, goal: Goal) -> bool:
        """更新目标"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE goals SET name = ?, category = ?, description = ?,
                               target_value = ?, current_value = ?, unit = ?,
                               deadline = ?, priority = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                goal.name, goal.category.value, goal.description,
                goal.target_value, goal.current_value, goal.unit,
                goal.deadline, goal.priority, goal.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_goal(self, goal_id: int) -> bool:
        """删除目标（软删除）"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'UPDATE goals SET is_active = 0 WHERE id = ?', (goal_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # 每日状态相关操作
    def save_daily_state(self, state: DailyState) -> int:
        """保存每日状态"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO daily_states 
                (date, mood, energy, stress, sleep_hours, sleep_quality,
                 focus, motivation, health, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                state.date.date() if state.date else date.today(),
                state.mood, state.energy, state.stress,
                state.sleep_hours, state.sleep_quality,
                state.focus, state.motivation, state.health, state.notes
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_daily_state(self, target_date: date) -> Optional[DailyState]:
        """获取指定日期的状态"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM daily_states WHERE date = ?', (target_date,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_daily_state(row)
            return None
    
    def get_recent_states(self, days: int = 30) -> List[DailyState]:
        """获取最近N天的状态"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM daily_states 
                WHERE date >= date('now', '-{} days')
                ORDER BY date DESC
            '''.format(days))
            return [self._row_to_daily_state(row) for row in cursor.fetchall()]
    
    # 每日活动相关操作
    def save_daily_activity(self, activity: DailyActivity) -> int:
        """保存每日活动"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO daily_activities 
                (date, activity_type, description, duration_minutes,
                 efficiency, progress, goal_id, satisfaction, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.date.date() if activity.date else date.today(),
                activity.activity_type.value, activity.description,
                activity.duration_minutes, activity.efficiency,
                activity.progress, activity.goal_id,
                activity.satisfaction, activity.notes
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_daily_activities(self, target_date: date) -> List[DailyActivity]:
        """获取指定日期的所有活动"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM daily_activities WHERE date = ? ORDER BY created_at',
                (target_date,)
            )
            return [self._row_to_daily_activity(row) for row in cursor.fetchall()]
    
    def get_goal_activities(self, goal_id: int, days: int = 30) -> List[DailyActivity]:
        """获取特定目标的最近活动"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM daily_activities 
                WHERE goal_id = ? AND date >= date('now', '-{} days')
                ORDER BY date DESC
            '''.format(days), (goal_id,))
            return [self._row_to_daily_activity(row) for row in cursor.fetchall()]
    
    # 预测相关操作
    def save_prediction(self, prediction: Prediction) -> int:
        """保存预测结果"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO predictions 
                (goal_id, prediction_date, target_date, success_probability,
                 productivity_score, key_factors, recommendations, 
                 model_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction.goal_id, prediction.prediction_date,
                prediction.target_date, prediction.success_probability,
                prediction.productivity_score,
                json.dumps(prediction.key_factors, ensure_ascii=False),
                json.dumps(prediction.recommendations, ensure_ascii=False),
                prediction.model_type, prediction.confidence
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_latest_prediction(self, goal_id: int) -> Optional[Prediction]:
        """获取目标的最新预测"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM predictions 
                WHERE goal_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (goal_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_prediction(row)
            return None
    
    def get_prediction_history(self, goal_id: int, limit: int = 10) -> List[Prediction]:
        """获取预测历史"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM predictions 
                WHERE goal_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (goal_id, limit))
            return [self._row_to_prediction(row) for row in cursor.fetchall()]
    
    # 模型指标相关操作
    def save_model_metrics(self, metrics: ModelMetrics) -> int:
        """保存模型性能指标"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO model_metrics 
                (model_type, accuracy, precision, recall, f1_score,
                 training_samples, last_trained)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.model_type, metrics.accuracy, metrics.precision,
                metrics.recall, metrics.f1_score, metrics.training_samples,
                metrics.last_trained
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_latest_model_metrics(self, model_type: str) -> Optional[ModelMetrics]:
        """获取最新的模型指标"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM model_metrics 
                WHERE model_type = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (model_type,))
            row = cursor.fetchone()
            if row:
                return self._row_to_model_metrics(row)
            return None
    
    # 数据转换辅助方法
    def _row_to_goal(self, row) -> Goal:
        """将数据库行转换为Goal对象"""
        return Goal(
            id=row['id'],
            name=row['name'],
            category=GoalCategory(row['category']),
            description=row['description'] or "",
            target_value=row['target_value'],
            current_value=row['current_value'],
            unit=row['unit'] or "",
            deadline=datetime.fromisoformat(row['deadline']) if row['deadline'] else None,
            priority=row['priority'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            is_active=bool(row['is_active'])
        )
    
    def _row_to_daily_state(self, row) -> DailyState:
        """将数据库行转换为DailyState对象"""
        return DailyState(
            id=row['id'],
            date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
            mood=row['mood'],
            energy=row['energy'],
            stress=row['stress'],
            sleep_hours=row['sleep_hours'],
            sleep_quality=row['sleep_quality'],
            focus=row['focus'],
            motivation=row['motivation'],
            health=row['health'],
            notes=row['notes'] or "",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def _row_to_daily_activity(self, row) -> DailyActivity:
        """将数据库行转换为DailyActivity对象"""
        return DailyActivity(
            id=row['id'],
            date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
            activity_type=ActivityType(row['activity_type']),
            description=row['description'] or "",
            duration_minutes=row['duration_minutes'],
            efficiency=row['efficiency'],
            progress=row['progress'],
            goal_id=row['goal_id'],
            satisfaction=row['satisfaction'],
            notes=row['notes'] or "",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def _row_to_prediction(self, row) -> Prediction:
        """将数据库行转换为Prediction对象"""
        return Prediction(
            id=row['id'],
            goal_id=row['goal_id'],
            prediction_date=datetime.fromisoformat(row['prediction_date']),
            target_date=datetime.fromisoformat(row['target_date']),
            success_probability=row['success_probability'],
            productivity_score=row['productivity_score'],
            key_factors=json.loads(row['key_factors']) if row['key_factors'] else {},
            recommendations=json.loads(row['recommendations']) if row['recommendations'] else [],
            model_type=row['model_type'],
            confidence=row['confidence'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def _row_to_model_metrics(self, row) -> ModelMetrics:
        """将数据库行转换为ModelMetrics对象"""
        return ModelMetrics(
            id=row['id'],
            model_type=row['model_type'],
            accuracy=row['accuracy'],
            precision=row['precision'],
            recall=row['recall'],
            f1_score=row['f1_score'],
            training_samples=row['training_samples'],
            last_trained=datetime.fromisoformat(row['last_trained']) if row['last_trained'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    # 统计查询方法
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据概览"""
        with self.get_connection() as conn:
            summary = {}
            
            # 目标统计
            cursor = conn.execute('SELECT COUNT(*) as count FROM goals WHERE is_active = 1')
            summary['active_goals'] = cursor.fetchone()['count']
            
            # 状态记录统计
            cursor = conn.execute('SELECT COUNT(*) as count FROM daily_states')
            summary['state_records'] = cursor.fetchone()['count']
            
            # 活动记录统计
            cursor = conn.execute('SELECT COUNT(*) as count FROM daily_activities')
            summary['activity_records'] = cursor.fetchone()['count']
            
            # 预测记录统计
            cursor = conn.execute('SELECT COUNT(*) as count FROM predictions')
            summary['prediction_records'] = cursor.fetchone()['count']
            
            # 最近7天的平均状态
            cursor = conn.execute('''
                SELECT AVG(mood) as avg_mood, AVG(energy) as avg_energy,
                       AVG(stress) as avg_stress, AVG(sleep_hours) as avg_sleep
                FROM daily_states 
                WHERE date >= date('now', '-7 days')
            ''')
            recent_avg = cursor.fetchone()
            summary['recent_averages'] = {
                'mood': round(recent_avg['avg_mood'] or 0, 1),
                'energy': round(recent_avg['avg_energy'] or 0, 1),
                'stress': round(recent_avg['avg_stress'] or 0, 1),
                'sleep': round(recent_avg['avg_sleep'] or 0, 1)
            }
            
            return summary