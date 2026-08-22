import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from aws_lambda_powertools import Logger
from sqlalchemy import and_, not_, or_

logger = Logger()


# 全局数据库引擎和会话工厂
engine = None
Session = None


@contextmanager
def session_scope():
    """提供事务范围的上下文管理器"""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_db():
    """在冷启动时初始化数据库连接"""
    global engine, Session

    try:
        # 创建连接字符串
        db_url = os.getenv('DATABASE_URL')

        # 创建引擎
        engine = create_engine(
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
        Session = scoped_session(
            sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False
            )
        )

        logger.info("Database connection initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}")
        raise


# 冷启动时初始化
try:
    initialize_db()
except Exception as e:
    logger.error(f"Initialization error: {str(e)}")

from sqlalchemy import Column, String, Text, Integer, SmallInteger, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

DEFAULT_COSTRATE = [0, 0, 0] # tax, shipping, duty
TAX_IN_PRICE_COUNTRIES = ['GB', 'AU', 'DE', 'FR', 'IT', 'ES']

class Costrate2(Base):
    __tablename__ = 'core_costrate2'

    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(2), nullable=False)
    state = Column(String(100), nullable=False)
    zipcode = Column(String(10), nullable=False)
    type = Column(String(1), nullable=False, default='')
    value = Column(Float, nullable=False)
    merchant_id = Column(String(100), nullable=False)
    category = Column(String(1), nullable=False, default='')
    subcategory = Column(String(100), nullable=False, default='')


class Costrate(Base):
    __tablename__ = 'core_costrate'

    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(2), nullable=False, default='')
    state = Column(String(100), nullable=False, default='')
    zipcode = Column(String(10), nullable=False, default='')
    merchant_id = Column(String(100), nullable=False)
    tax = Column(Float, nullable=False, default=0.12)
    shipping = Column(Float, nullable=False, default=0)
    duty = Column(Float, nullable=False, default=0)

    @staticmethod
    def get_tax_rate(session, country, merchant_id):
        rates = {
            '': 1
        }

        if country.upper() not in TAX_IN_PRICE_COUNTRIES:
            return rates

        costrates = session.query(Costrate2).filter(
            and_(
                Costrate2.country == country,
                Costrate2.merchant_id == merchant_id,
                Costrate2.type == 't',
                Costrate2.zipcode == ''
            )
        ).all()

        for costrate in costrates:
            if costrate.value > 0:
                if costrate.category:
                    rates[costrate.category] = 1 + costrate.value
                else:
                    rates[''] = 1 + costrate.value

        return rates


class Availability(Base):
    __tablename__ = 'product_availability'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer)
    designer_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    gender = Column(String(1), nullable=False)
    category = Column(String(1), nullable=False)
    seccategory = Column(String(50), nullable=False, server_default='')
    subcategory = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    color = Column(String(100), nullable=False)
    cover = Column(String(500), nullable=False)
    condition = Column(String(1), nullable=False, server_default='')
    code = Column(String(100), nullable=False)
    styleid = Column(String(50), nullable=False, server_default='')
    merchant_id = Column(String(100), nullable=False)
    listprice = Column(Float, nullable=False)
    saleprice = Column(Float, nullable=False)
    saleprice_max = Column(Float)
    discount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    sizes = Column(String(200), nullable=False, server_default='')
    link = Column(String(400), nullable=False)
    opened = Column(Integer, nullable=False)
    update_datetime = Column(DateTime, nullable=False)
    create_datetime = Column(DateTime, nullable=False)
    rs_datetime = Column(DateTime)
    checkby_id = Column(Integer, nullable=False, server_default='1')
    removed = Column(Boolean, nullable=False)
    resolving = Column(Boolean, nullable=False, server_default='0')
    stage = Column(SmallInteger, nullable=False, server_default='0')
    colorcount = Column(TINYINT(), nullable=False, server_default='0')
    red1 = Column(TINYINT(), nullable=False, server_default='0')
    green1 = Column(TINYINT(), nullable=False, server_default='0')
    blue1 = Column(TINYINT(), nullable=False, server_default='0')
    red2 = Column(TINYINT(), nullable=False, server_default='0')
    green2 = Column(TINYINT(), nullable=False, server_default='0')
    blue2 = Column(TINYINT(), nullable=False, server_default='0')
    orisizes = Column(String(1000), nullable=False, server_default='')
    saved_to_s3 = Column(Boolean, server_default='0')
    changed = Column(Boolean, server_default='1')
    color_ori = Column(String(100), nullable=False)

    __table_args__ = (
        {'mysql_charset': 'utf8mb3', 'mysql_collate': 'utf8mb3_unicode_ci', 'mysql_row_format': 'DYNAMIC'}
    )

class Merchant(Base):
    __tablename__ = 'product_merchant'

    name = Column(String(100), primary_key=True)
    name_url = Column(String(100))
    name_display = Column(String(100), server_default='')
    typ = Column(String(1), server_default='p')
    categories = Column(String(10), nullable=False)
    alias = Column(String(100), nullable=False)
    logo = Column(String(200), server_default='')
    website = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    mcount = Column(Integer, server_default='0')
    fcount = Column(Integer, server_default='0')
    referral_link = Column(String(200), nullable=False)
    sssupport = Column(Boolean, server_default='0')
    rssupport = Column(Boolean, server_default='0')
    cjsupport = Column(Boolean, server_default='0')
    lssupport = Column(Boolean, server_default='0')
    phsupport = Column(Boolean, server_default='0')
    tdsupport = Column(Boolean, server_default='0')
    vgsupport = Column(Boolean, server_default='0')
    sksupport = Column(Boolean, server_default='0')
    platform = Column(String(2), server_default='')
    lsprefix = Column(String(200), server_default='')
    postfix = Column(String(200), server_default='')
    viewed = Column(Integer, server_default='0')
    liked = Column(Integer, server_default='0')
    opened = Column(Integer, server_default='0')
    rates = Column(Integer, server_default='0')
    rating = Column(SmallInteger(), server_default='0')
    rated = Column(Integer, server_default='0')
    overall = Column(Float, server_default='0')
    ship = Column(SmallInteger(), server_default='0')
    retrn = Column(SmallInteger(), server_default='0')
    support = Column(SmallInteger(), server_default='0')
    test_link = Column(String(500), nullable=False)
    lsuser_id = Column(Integer)
    commission = Column(SmallInteger(), server_default='0')
    boost = Column(SmallInteger(), server_default='0')
    duty = Column(SmallInteger, server_default='0')
    shipping = Column(String(100), server_default='')
    removed = Column(Boolean, nullable=False)
    mid = Column(String(20), server_default='')
    clicks = Column(Integer, nullable=False)
    clicksms = Column(Integer, nullable=False)
    orders = Column(Integer, nullable=False)
    items = Column(Integer, nullable=False)
    sales = Column(Float, server_default='0')
    commissions = Column(Float, server_default='0')
    epc = Column(Float, server_default='0')
    epc_approve = Column(Float, server_default='0')
    approve_rate = Column(Float, server_default='-1')
    score = Column(Float, server_default='-1')
    shippingcost = Column(Float, server_default='0')
    preview = Column(Boolean, server_default='1')
    all_designer_flag = Column(Boolean, server_default='1')
    facount = Column(Integer, server_default='0')
    fbcount = Column(Integer, server_default='0')
    fccount = Column(Integer, server_default='0')
    fscount = Column(Integer, server_default='0')
    fecount = Column(Integer, server_default='0')
    macount = Column(Integer, server_default='0')
    mbcount = Column(Integer, server_default='0')
    mccount = Column(Integer, server_default='0')
    mscount = Column(Integer, server_default='0')
    mecount = Column(Integer, server_default='0')
    hcount = Column(Integer, server_default='0')
    block_assist = Column(Boolean, server_default='0')
    block_assist_points = Column(Boolean, server_default='0')
    block_assist_full = Column(Boolean, server_default='0')
    noindex = Column(Boolean, server_default='0')
    merged_to_id = Column(String(100), ForeignKey('product_merchant.name'))
    quality = Column(SmallInteger, nullable=False)
    city = Column(String(50), nullable=False)
    country = Column(String(2), nullable=False)
    terms = Column(Text, nullable=False)
    scan = Column(Text)
    realtime = Column(Boolean, server_default='0')
    customer_service_email = Column(String(254), nullable=False)
    qa_support = Column(Boolean, server_default='1')
    name_url_old = Column(String(100), server_default='')
    newcount = Column(Integer, server_default='0')
    preownedcount = Column(Integer, server_default='0')
    common_account = Column(Boolean, server_default='0')
    order_instruction = Column(Text)
    nocoupons = Column(Boolean, server_default='0')
    noreviews = Column(Boolean, server_default='0')
    checkout_block = Column(SmallInteger, server_default='0')
    boost_to = Column(DateTime(6), nullable=False)
    checkout_approved = Column(Boolean, server_default='0')
    merge_block = Column(Boolean, server_default='0')
    order_term = Column(Text, nullable=False)
    fast_shipping = Column(SmallInteger(), server_default='0')
    easy_return = Column(SmallInteger(), server_default='0')
    good_service = Column(SmallInteger(), server_default='0')
    kcount = Column(Integer(), server_default='0')

    __table_args__ = (
        {'mysql_charset': 'utf8mb3', 'mysql_collate': 'utf8mb3_unicode_ci'}
    )