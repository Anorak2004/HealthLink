"""
数据库切换配置模块
支持 SQLite -> MySQL 无缝切换
"""
import os
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_database_url(config: Dict[str, Any]) -> str:
    """根据配置生成数据库URL"""
    db_config = config['database']
    db_type = db_config['type']
    
    if db_type == 'sqlite':
        db_path = db_config['sqlite']['path']
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"
    
    elif db_type == 'mysql':
        mysql_config = db_config['mysql']
        host = mysql_config['host']
        port = mysql_config['port']
        database = mysql_config['database']
        username = os.getenv('MYSQL_USER', mysql_config['username'])
        password = os.getenv('MYSQL_PASSWORD', mysql_config['password'])
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    
    elif db_type == 'postgresql':
        # 预留PostgreSQL支持
        pg_config = db_config.get('postgresql', {})
        host = pg_config.get('host', 'localhost')
        port = pg_config.get('port', 5432)
        database = pg_config.get('database', 'healthlink')
        username = os.getenv('POSTGRES_USER', pg_config.get('username'))
        password = os.getenv('POSTGRES_PASSWORD', pg_config.get('password'))
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def create_database_engine(config: Dict[str, Any]):
    """创建数据库引擎"""
    database_url = get_database_url(config)
    db_config = config['database']
    
    engine_kwargs = {}
    
    if db_config['type'] == 'sqlite':
        engine_kwargs.update({
            'echo': db_config['sqlite'].get('echo', False),
            'connect_args': {'check_same_thread': False}
        })
    elif db_config['type'] == 'mysql':
        mysql_config = db_config['mysql']
        engine_kwargs.update({
            'pool_size': mysql_config.get('pool_size', 10),
            'max_overflow': mysql_config.get('max_overflow', 20),
            'pool_pre_ping': True,
            'pool_recycle': 3600
        })
    
    engine = create_engine(database_url, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

# 全局配置实例
_config = None
_engine = None
_session_local = None

def get_config():
    """获取全局配置"""
    global _config
    if _config is None:
        _config = load_config()
    return _config

def get_database():
    """获取数据库会话"""
    global _engine, _session_local
    if _engine is None or _session_local is None:
        config = get_config()
        _engine, _session_local = create_database_engine(config)
    
    db = _session_local()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """初始化数据库表"""
    from packages.schemas.models import Base  # 导入所有模型
    config = get_config()
    engine, _ = create_database_engine(config)
    Base.metadata.create_all(bind=engine)
    return engine