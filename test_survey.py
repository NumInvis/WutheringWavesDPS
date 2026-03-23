#!/usr/bin/env python3
"""测试问卷系统"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.survey import Survey, SurveyQuestion, SurveyOption, QuestionType, SurveyStatus
from app.models.user import User
from sqlalchemy import inspect
from datetime import datetime

def check_tables():
    """检查表是否存在"""
    inspector = inspect(engine)
    print("=== 检查数据库表 ===")
    tables = inspector.get_table_names()
    print(f"现有表: {tables}")
    
    required_tables = ['surveys', 'survey_questions', 'survey_options', 'survey_responses', 'survey_answers']
    for table in required_tables:
        if table in tables:
            print(f"✅ {table} 存在")
        else:
            print(f"❌ {table} 不存在")
    
    return all(table in tables for table in required_tables)

def create_test_survey():
    """创建测试问卷"""
    db = SessionLocal()
    try:
        # 获取管理员用户
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            print("❌ 没有找到管理员用户")
            return
        
        print(f"✅ 使用管理员: {admin.username}")
        
        # 创建测试问卷
        survey = Survey(
            title="测试问卷",
            description="这是一个测试问卷，用于验证系统功能",
            status=SurveyStatus.PUBLISHED.value,
            allow_anonymous=True,
            allow_multiple=False,
            created_by=admin.id
        )
        db.add(survey)
        db.flush()
        
        # 创建问题1 - 单选题
        q1 = SurveyQuestion(
            survey_id=survey.id,
            title="你喜欢玩游戏吗？",
            question_type=QuestionType.SINGLE_CHOICE.value,
            is_required=True,
            order=0
        )
        db.add(q1)
        db.flush()
        
        # 添加选项
        opt1_1 = SurveyOption(question_id=q1.id, content="喜欢", order=0)
        opt1_2 = SurveyOption(question_id=q1.id, content="不喜欢", order=1)
        opt1_3 = SurveyOption(question_id=q1.id, content="一般", order=2)
        db.add_all([opt1_1, opt1_2, opt1_3])
        
        # 创建问题2 - 多选题
        q2 = SurveyQuestion(
            survey_id=survey.id,
            title="你喜欢什么类型的游戏？",
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            is_required=True,
            order=1
        )
        db.add(q2)
        db.flush()
        
        # 添加选项
        opt2_1 = SurveyOption(question_id=q2.id, content="动作", order=0)
        opt2_2 = SurveyOption(question_id=q2.id, content="角色扮演", order=1)
        opt2_3 = SurveyOption(question_id=q2.id, content="策略", order=2)
        opt2_4 = SurveyOption(question_id=q2.id, content="休闲", order=3)
        db.add_all([opt2_1, opt2_2, opt2_3, opt2_4])
        
        # 创建问题3 - 评分题
        q3 = SurveyQuestion(
            survey_id=survey.id,
            title="你对我们的网站满意吗？",
            question_type=QuestionType.RATING.value,
            is_required=True,
            order=2,
            config={"max_rating": 5}
        )
        db.add(q3)
        
        # 创建问题4 - 填空题
        q4 = SurveyQuestion(
            survey_id=survey.id,
            title="请留下您的宝贵意见",
            question_type=QuestionType.FILL_IN_BLANK.value,
            is_required=False,
            order=3,
            config={"placeholder": "请输入您的意见", "max_length": 500}
        )
        db.add(q4)
        
        db.commit()
        print(f"✅ 测试问卷创建成功！ID: {survey.id}")
        return survey.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建测试问卷失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def list_surveys():
    """列出所有问卷"""
    db = SessionLocal()
    try:
        surveys = db.query(Survey).all()
        print(f"\n=== 现有问卷 ({len(surveys)}) ===")
        for s in surveys:
            print(f"- {s.title} ({s.status}) - {len(s.questions)} 个问题 - {s.total_responses} 次填写")
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 问卷系统测试 ===\n")
    
    # 检查数据库表
    tables_ok = check_tables()
    if not tables_ok:
        print("\n⚠️ 尝试创建表...")
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ 表创建成功！")
            # 再次检查
            check_tables()
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 列出现有问卷
    list_surveys()
    
    # 询问是否创建测试问卷
    print("\n是否创建测试问卷？(y/n)")
    choice = input().strip().lower()
    if choice == 'y':
        survey_id = create_test_survey()
        if survey_id:
            list_surveys()
