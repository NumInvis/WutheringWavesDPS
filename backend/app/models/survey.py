"""
问卷系统模型
支持创建问卷、问题、选项，以及用户填写记录
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum
from .base import Base, TimestampMixin


class QuestionType(str, enum.Enum):
    """问题类型枚举"""
    SINGLE_CHOICE = "single_choice"  # 单选
    MULTIPLE_CHOICE = "multiple_choice"  # 多选
    FILL_IN_BLANK = "fill_in_blank"  # 填空
    RATING = "rating"  # 评分


class SurveyStatus(str, enum.Enum):
    """问卷状态枚举"""
    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    CLOSED = "closed"  # 已关闭
    PAUSED = "paused"  # 暂停


class Survey(Base, TimestampMixin):
    """问卷表"""
    __tablename__ = "surveys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)  # 问卷标题
    description = Column(Text)  # 问卷描述
    status = Column(String(20), default=SurveyStatus.DRAFT.value)  # 状态
    
    # 时间设置
    start_time = Column(DateTime)  # 开始时间，None表示立即开始
    end_time = Column(DateTime)  # 结束时间，None表示无限期
    
    # 填写设置
    allow_anonymous = Column(Boolean, default=False)  # 是否允许匿名填写
    allow_multiple = Column(Boolean, default=False)  # 是否允许同一用户多次填写
    max_responses = Column(Integer)  # 最大填写次数限制，None表示无限制
    
    # 创建者
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 统计
    total_responses = Column(Integer, default=0)  # 总填写次数
    
    # 关系
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class SurveyQuestion(Base, TimestampMixin):
    """问卷问题表"""
    __tablename__ = "survey_questions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False)
    
    title = Column(String(500), nullable=False)  # 问题标题
    description = Column(Text)  # 问题描述/说明
    question_type = Column(String(20), nullable=False)  # 问题类型
    
    # 排序
    order = Column(Integer, default=0)
    
    # 是否必填
    is_required = Column(Boolean, default=True)
    
    # 额外配置（JSON格式，用于存储评分范围、填空验证等）
    config = Column(JSON, default=dict)
    # config示例:
    # {
    #     "min_rating": 1,      # 评分最小值
    #     "max_rating": 5,      # 评分最大值
    #     "placeholder": "请输入...",  # 填空提示
    #     "validation": "email", # 验证类型：email, phone, number, text
    #     "max_length": 500     # 最大长度
    # }
    
    # 关系
    survey = relationship("Survey", back_populates="questions")
    options = relationship("SurveyOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("SurveyAnswer", back_populates="question", cascade="all, delete-orphan")


class SurveyOption(Base, TimestampMixin):
    """问题选项表（用于单选/多选）"""
    __tablename__ = "survey_options"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("survey_questions.id"), nullable=False)
    
    content = Column(String(500), nullable=False)  # 选项内容
    order = Column(Integer, default=0)  # 排序
    
    # 关系
    question = relationship("SurveyQuestion", back_populates="options")
    answers = relationship("SurveyAnswer", back_populates="selected_option")


class SurveyResponse(Base, TimestampMixin):
    """问卷填写记录表"""
    __tablename__ = "survey_responses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False)
    
    # 填写者信息
    user_id = Column(String(36), ForeignKey("users.id"))  # 用户ID，匿名时为None
    user_ip = Column(String(50))  # 用户IP（用于匿名用户防重复）
    
    # 填写时间
    started_at = Column(DateTime, default=datetime.utcnow)  # 开始填写时间
    submitted_at = Column(DateTime)  # 提交时间
    
    # 状态
    is_submitted = Column(Boolean, default=False)  # 是否已提交
    is_anonymous = Column(Boolean, default=False)  # 是否匿名填写
    
    # 关系
    survey = relationship("Survey", back_populates="responses")
    user = relationship("User", foreign_keys=[user_id])
    answers = relationship("SurveyAnswer", back_populates="response", cascade="all, delete-orphan")


class SurveyAnswer(Base, TimestampMixin):
    """问卷答案表"""
    __tablename__ = "survey_answers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    response_id = Column(String(36), ForeignKey("survey_responses.id"), nullable=False)
    question_id = Column(String(36), ForeignKey("survey_questions.id"), nullable=False)
    
    # 答案内容
    # 单选：存储选项ID
    # 多选：存储选项ID列表（JSON）
    # 填空：存储文本内容
    # 评分：存储评分值
    answer_content = Column(Text)  # 答案内容（文本形式）
    answer_data = Column(JSON, default=dict)  # 答案数据（结构化）
    # answer_data示例:
    # {
    #     "type": "single_choice",
    #     "option_id": "uuid",
    #     "text": "选项内容"
    # }
    # 或
    # {
    #     "type": "multiple_choice",
    #     "option_ids": ["uuid1", "uuid2"],
    #     "texts": ["选项1", "选项2"]
    # }
    # 或
    # {
    #     "type": "fill_in_blank",
    #     "text": "用户输入的内容"
    # }
    # 或
    # {
    #     "type": "rating",
    #     "value": 4
    # }
    
    # 单选时关联的选项
    selected_option_id = Column(String(36), ForeignKey("survey_options.id"))
    
    # 关系
    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion", back_populates="answers")
    selected_option = relationship("SurveyOption", back_populates="answers")
