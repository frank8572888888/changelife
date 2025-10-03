"""
数据模型定义
定义目标、状态、行为等核心数据结构
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class GoalCategory(Enum):
    """目标类别"""
    LEARNING = "学习"
    FITNESS = "健身"
    WORK = "工作"
    PERSONAL = "个人发展"
    HEALTH = "健康"
    RELATIONSHIP = "人际关系"
    FINANCE = "财务"
    HOBBY = "兴趣爱好"


class StateType(Enum):
    """状态类型"""
    MOOD = "心情"
    ENERGY = "精力"
    STRESS = "压力"
    SLEEP = "睡眠"
    FOCUS = "专注度"
    MOTIVATION = "动机"
    HEALTH = "健康状况"


class ActivityType(Enum):
    """活动类型"""
    STUDY = "学习"
    EXERCISE = "运动"
    WORK = "工作"
    REST = "休息"
    SOCIAL = "社交"
    ENTERTAINMENT = "娱乐"
    HOUSEWORK = "家务"
    COMMUTE = "通勤"


@dataclass
class Goal:
    """目标数据模型"""
    id: Optional[int] = None
    name: str = ""
    category: GoalCategory = GoalCategory.PERSONAL
    description: str = ""
    target_value: float = 0.0
    current_value: float = 0.0
    unit: str = ""
    deadline: Optional[datetime] = None
    priority: int = 1  # 1-5, 5最高
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class DailyState:
    """每日状态数据模型"""
    id: Optional[int] = None
    date: datetime = None
    mood: int = 5  # 1-10评分
    energy: int = 5  # 1-10评分
    stress: int = 5  # 1-10评分，10为最高压力
    sleep_hours: float = 8.0
    sleep_quality: int = 5  # 1-10评分
    focus: int = 5  # 1-10评分
    motivation: int = 5  # 1-10评分
    health: int = 5  # 1-10评分
    notes: str = ""
    created_at: Optional[datetime] = None


@dataclass
class DailyActivity:
    """每日活动数据模型"""
    id: Optional[int] = None
    date: datetime = None
    activity_type: ActivityType = ActivityType.WORK
    description: str = ""
    duration_minutes: int = 0
    efficiency: int = 5  # 1-10评分
    progress: float = 0.0  # 完成度百分比
    goal_id: Optional[int] = None  # 关联的目标ID
    satisfaction: int = 5  # 1-10评分
    notes: str = ""
    created_at: Optional[datetime] = None


@dataclass
class Prediction:
    """预测结果数据模型"""
    id: Optional[int] = None
    goal_id: int = 0
    prediction_date: datetime = None
    target_date: datetime = None  # 预测的目标日期
    success_probability: float = 0.0  # 成功概率 0-1
    productivity_score: float = 0.0  # 生产力评分 0-10
    key_factors: Dict[str, float] = None  # 关键影响因素及权重
    recommendations: List[str] = None  # 改进建议
    model_type: str = "heuristic"  # heuristic, ml, ai
    confidence: float = 0.0  # 预测置信度
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.key_factors is None:
            self.key_factors = {}
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class ModelMetrics:
    """模型性能指标"""
    id: Optional[int] = None
    model_type: str = ""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    training_samples: int = 0
    last_trained: Optional[datetime] = None
    created_at: Optional[datetime] = None


# 数据库表结构定义
DATABASE_SCHEMA = {
    'goals': '''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            target_value REAL DEFAULT 0.0,
            current_value REAL DEFAULT 0.0,
            unit TEXT DEFAULT '',
            deadline DATETIME,
            priority INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''',
    
    'daily_states': '''
        CREATE TABLE IF NOT EXISTS daily_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            mood INTEGER DEFAULT 5,
            energy INTEGER DEFAULT 5,
            stress INTEGER DEFAULT 5,
            sleep_hours REAL DEFAULT 8.0,
            sleep_quality INTEGER DEFAULT 5,
            focus INTEGER DEFAULT 5,
            motivation INTEGER DEFAULT 5,
            health INTEGER DEFAULT 5,
            notes TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'daily_activities': '''
        CREATE TABLE IF NOT EXISTS daily_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT,
            duration_minutes INTEGER DEFAULT 0,
            efficiency INTEGER DEFAULT 5,
            progress REAL DEFAULT 0.0,
            goal_id INTEGER,
            satisfaction INTEGER DEFAULT 5,
            notes TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''',
    
    'predictions': '''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            prediction_date DATETIME NOT NULL,
            target_date DATETIME NOT NULL,
            success_probability REAL DEFAULT 0.0,
            productivity_score REAL DEFAULT 0.0,
            key_factors TEXT,  -- JSON格式存储
            recommendations TEXT,  -- JSON格式存储
            model_type TEXT DEFAULT 'heuristic',
            confidence REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''',
    
    'model_metrics': '''
        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_type TEXT NOT NULL,
            accuracy REAL DEFAULT 0.0,
            precision REAL DEFAULT 0.0,
            recall REAL DEFAULT 0.0,
            f1_score REAL DEFAULT 0.0,
            training_samples INTEGER DEFAULT 0,
            last_trained DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    '''
}