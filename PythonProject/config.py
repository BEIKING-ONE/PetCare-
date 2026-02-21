"""
配置文件
文件名：config.py
"""

import os


class Config:
    # 基础配置
    SECRET_KEY = 'your-secret-key-here-change-in-production'
    DEBUG = True

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/pet_platform?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 跨域配置
    CORS_ORIGINS = '*'

    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # JWT配置（简化版）
    JWT_SECRET = 'jwt-secret-key-change-in-production'
    JWT_EXPIRE_DAYS = 7

    # 微信小程序配置（需要替换为实际值）
    WX_APP_ID = 'your-wechat-app-id'
    WX_APP_SECRET = 'your-wechat-app-secret'


# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/pet_platform_test?charset=utf8mb4'