import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from aws_lambda_powertools import Logger
from sqlalchemy import and_, not_, or_

logger = Logger()


# 全局数据库引擎和会话工厂
engine_lsmerge = None
Session_lsmerge = None


@contextmanager
def session_scope():
    """提供事务范围的上下文管理器"""
    session = Session_lsmerge()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_db_lsmerge():
    """在冷启动时初始化数据库连接"""
    global engine_lsmerge, Session_lsmerge

    try:
        # 创建连接字符串
        db_url = os.getenv('DATABASE_URL_LSMERGE')

        # 创建引擎
        engine_lsmerge = create_engine(
            db_url,
            pool_size=5,  # 连接池大小
            max_overflow=2,  # 允许超过pool_size的临时连接数
            pool_recycle=300,  # 连接回收时间(秒)
            pool_pre_ping=True,  # 执行前检查连接是否有效
            connect_args={
                'connect_timeout': 5  # 连接超时5秒
            }
        )

        # 创建scoped session工厂
        Session_lsmerge = scoped_session(
            sessionmaker(
                bind=engine_lsmerge,
                autocommit=False,
                autoflush=False
            )
        )

        logger.info("Database lsmerge connection initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database lsmerge connection: {str(e)}")
        raise


# 冷启动时初始化
try:
    initialize_db_lsmerge()
except Exception as e:
    logger.error(f"Initialization lsmerge error: {str(e)}")

from sqlalchemy import Column, String, Text, Integer, SmallInteger, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class SizeExtra(Base):
    __tablename__ = 'sizeextra'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer)
    avail_id = Column(Integer)
    merchant_id = Column(String(100), nullable=False)
    link = Column(String(400), nullable=False)
    size_json = Column(String(1000), nullable=False, server_default='')
    currency = Column(String(3), nullable=False)
    category = Column(String(20), nullable=False)
    default_list_price = Column(Float, nullable=False)
    default_sale_price = Column(Float, nullable=False)
    ls_list_price = Column(Float, nullable=False)
    ls_sale_price = Column(Float, nullable=False)
    update_datetime = Column(DateTime, nullable=False)
    create_datetime = Column(DateTime, nullable=False)
