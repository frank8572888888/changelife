"""
系统配置文件
"""
import os
from typing import Dict, Any


class Config:
    """系统配置类"""
    
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/goals.db')
    
    # 模型配置
    MODEL_DIR = os.getenv('MODEL_DIR', 'models')
    MIN_TRAINING_SAMPLES = int(os.getenv('MIN_TRAINING_SAMPLES', '30'))
    
    # API配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    
    # 预测配置
    DEFAULT_PREDICTION_STRATEGY = os.getenv('PREDICTION_STRATEGY', 'auto')  # auto, heuristic, ml, ai
    PREDICTION_CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.6'))
    
    # 数据质量配置
    MIN_STATE_RECORDS_FOR_ML = int(os.getenv('MIN_STATE_RECORDS', '14'))
    MIN_ACTIVITY_RECORDS_FOR_ML = int(os.getenv('MIN_ACTIVITY_RECORDS', '21'))
    DATA_FRESHNESS_DAYS = int(os.getenv('DATA_FRESHNESS_DAYS', '7'))
    
    # 报告配置
    REPORT_DIR = os.getenv('REPORT_DIR', 'reports')
    CHART_DIR = os.getenv('CHART_DIR', 'charts')
    ENABLE_CHARTS = os.getenv('ENABLE_CHARTS', 'true').lower() == 'true'
    
    # 日志配置
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # UI配置
    CLI_LANGUAGE = os.getenv('CLI_LANGUAGE', 'zh')  # zh, en
    PROGRESS_BAR_WIDTH = int(os.getenv('PROGRESS_BAR_WIDTH', '20'))
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        config = {}
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)):
                config[attr] = getattr(cls, attr)
        return config
    
    @classmethod
    def validate_config(cls) -> Dict[str, str]:
        """验证配置"""
        issues = []
        
        # 检查必要目录
        required_dirs = [
            cls.MODEL_DIR,
            cls.REPORT_DIR, 
            cls.CHART_DIR,
            cls.LOG_DIR
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    issues.append(f"无法创建目录 {directory}: {e}")
        
        # 检查数据库目录
        db_dir = os.path.dirname(cls.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                issues.append(f"无法创建数据库目录 {db_dir}: {e}")
        
        # 检查API密钥
        if not cls.DEEPSEEK_API_KEY:
            issues.append("未设置DEEPSEEK_API_KEY，AI功能将不可用")
        
        # 检查数值配置
        if cls.MIN_TRAINING_SAMPLES < 10:
            issues.append("MIN_TRAINING_SAMPLES过小，建议至少设置为30")
        
        if cls.PREDICTION_CONFIDENCE_THRESHOLD < 0 or cls.PREDICTION_CONFIDENCE_THRESHOLD > 1:
            issues.append("CONFIDENCE_THRESHOLD应在0-1之间")
        
        return issues


# 创建全局配置实例
config = Config()


# 预定义的配置模板
CONFIG_TEMPLATES = {
    "development": {
        "LOG_LEVEL": "DEBUG",
        "ENABLE_CHARTS": "true",
        "MIN_TRAINING_SAMPLES": "20"
    },
    
    "production": {
        "LOG_LEVEL": "INFO", 
        "ENABLE_CHARTS": "false",
        "MIN_TRAINING_SAMPLES": "50"
    },
    
    "minimal": {
        "ENABLE_CHARTS": "false",
        "MIN_TRAINING_SAMPLES": "10",
        "PREDICTION_STRATEGY": "heuristic"
    }
}


def load_config_template(template_name: str) -> bool:
    """加载配置模板"""
    if template_name not in CONFIG_TEMPLATES:
        return False
    
    template = CONFIG_TEMPLATES[template_name]
    for key, value in template.items():
        os.environ[key] = value
    
    # 重新加载配置
    global config
    config = Config()
    return True


def save_config_to_file(filepath: str = "config.env") -> bool:
    """保存当前配置到文件"""
    try:
        current_config = Config.get_all_config()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 智能目标检测系统配置文件\n")
            f.write(f"# 生成时间: {os.environ.get('TZ', 'UTC')}\n\n")
            
            for key, value in current_config.items():
                if value is not None:
                    f.write(f"{key}={value}\n")
        
        return True
    except Exception:
        return False


def load_config_from_file(filepath: str = "config.env") -> bool:
    """从文件加载配置"""
    try:
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        
        # 重新加载配置
        global config
        config = Config()
        return True
    except Exception:
        return False