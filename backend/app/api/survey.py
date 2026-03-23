"""
问卷系统API
提供问卷的创建、管理、填写和统计功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.survey import (
    Survey, SurveyQuestion, SurveyOption, SurveyResponse, SurveyAnswer,
    QuestionType, SurveyStatus
)
from app.models.user import User
from app.api.auth import get_current_active_user, get_current_user_optional
from app.core.logger import add_log

router = APIRouter(prefix="/api/surveys", tags=["问卷系统"])


# ========== Pydantic模型 ==========
from pydantic import BaseModel, Field


class SurveyOptionCreate(BaseModel):
    content: str
    order: int = 0


class SurveyQuestionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    question_type: str  # single_choice, multiple_choice, fill_in_blank, rating
    is_required: bool = True
    order: int = 0
    config: Optional[dict] = {}
    options: Optional[List[SurveyOptionCreate]] = []


class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    allow_anonymous: bool = False
    allow_multiple: bool = False
    max_responses: Optional[int] = None
    questions: List[SurveyQuestionCreate]


class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    allow_anonymous: Optional[bool] = None
    allow_multiple: Optional[bool] = None
    max_responses: Optional[int] = None
    questions: Optional[List[SurveyQuestionCreate]] = None


class AnswerSubmit(BaseModel):
    question_id: str
    answer_data: dict  # 根据问题类型不同，格式不同


class SurveySubmit(BaseModel):
    answers: List[AnswerSubmit]
    is_anonymous: bool = False


# ========== 管理员API ==========

@router.post("/admin/create")
async def create_survey(
    data: SurveyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新问卷（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以创建问卷")
    
    survey = Survey(
        id=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        status=SurveyStatus.DRAFT.value,
        start_time=data.start_time,
        end_time=data.end_time,
        allow_anonymous=data.allow_anonymous,
        allow_multiple=data.allow_multiple,
        max_responses=data.max_responses,
        created_by=current_user.id
    )
    
    db.add(survey)
    
    # 创建问题
    for q_data in data.questions:
        question = SurveyQuestion(
            id=str(uuid.uuid4()),
            survey_id=survey.id,
            title=q_data.title,
            description=q_data.description,
            question_type=q_data.question_type,
            is_required=q_data.is_required,
            order=q_data.order,
            config=q_data.config or {}
        )
        db.add(question)
        
        # 创建选项（单选/多选）
        if q_data.question_type in [QuestionType.SINGLE_CHOICE.value, QuestionType.MULTIPLE_CHOICE.value]:
            for opt_data in q_data.options:
                option = SurveyOption(
                    id=str(uuid.uuid4()),
                    question_id=question.id,
                    content=opt_data.content,
                    order=opt_data.order
                )
                db.add(option)
    
    db.commit()
    add_log("info", f"管理员 {current_user.username} 创建了问卷: {data.title}")
    
    return {"message": "问卷创建成功", "survey_id": survey.id}


@router.get("/admin/list")
async def list_surveys_admin(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取问卷列表（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看所有问卷")
    
    query = db.query(Survey)
    
    if status:
        query = query.filter(Survey.status == status)
    
    total = query.count()
    surveys = query.order_by(desc(Survey.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for s in surveys:
        result.append({
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "status": s.status,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "allow_anonymous": s.allow_anonymous,
            "allow_multiple": s.allow_multiple,
            "total_responses": s.total_responses,
            "created_at": s.created_at.isoformat(),
            "question_count": len(s.questions)
        })
    
    return {"surveys": result, "total": total, "page": page, "page_size": page_size}


@router.get("/admin/{survey_id}")
async def get_survey_admin(
    survey_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取问卷详情（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看问卷详情")
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    questions = []
    for q in sorted(survey.questions, key=lambda x: x.order):
        q_data = {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "question_type": q.question_type,
            "is_required": q.is_required,
            "order": q.order,
            "config": q.config
        }
        
        if q.question_type in [QuestionType.SINGLE_CHOICE.value, QuestionType.MULTIPLE_CHOICE.value]:
            q_data["options"] = [
                {"id": opt.id, "content": opt.content, "order": opt.order}
                for opt in sorted(q.options, key=lambda x: x.order)
            ]
        
        questions.append(q_data)
    
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "status": survey.status,
        "start_time": survey.start_time.isoformat() if survey.start_time else None,
        "end_time": survey.end_time.isoformat() if survey.end_time else None,
        "allow_anonymous": survey.allow_anonymous,
        "allow_multiple": survey.allow_multiple,
        "max_responses": survey.max_responses,
        "total_responses": survey.total_responses,
        "created_at": survey.created_at.isoformat(),
        "questions": questions
    }


@router.put("/admin/{survey_id}")
async def update_survey(
    survey_id: str,
    data: SurveyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新问卷（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以更新问卷")
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    if data.title is not None:
        survey.title = data.title
    if data.description is not None:
        survey.description = data.description
    if data.status is not None:
        survey.status = data.status
    if data.start_time is not None:
        survey.start_time = data.start_time
    if data.end_time is not None:
        survey.end_time = data.end_time
    if data.allow_anonymous is not None:
        survey.allow_anonymous = data.allow_anonymous
    if data.allow_multiple is not None:
        survey.allow_multiple = data.allow_multiple
    if data.max_responses is not None:
        survey.max_responses = data.max_responses
    
    # 如果提供了问题数据，则更新问题
    if data.questions is not None:
        # 删除旧的问题和选项
        for old_question in survey.questions:
            # 先删除选项
            for old_option in old_question.options:
                db.delete(old_option)
            db.delete(old_question)
        
        # 创建新的问题
        for q_data in data.questions:
            question = SurveyQuestion(
                id=str(uuid.uuid4()),
                survey_id=survey.id,
                title=q_data.title,
                description=q_data.description,
                question_type=q_data.question_type,
                is_required=q_data.is_required,
                order=q_data.order,
                config=q_data.config or {}
            )
            db.add(question)
            
            # 创建选项（单选/多选）
            if q_data.question_type in [QuestionType.SINGLE_CHOICE.value, QuestionType.MULTIPLE_CHOICE.value]:
                for opt_data in q_data.options:
                    option = SurveyOption(
                        id=str(uuid.uuid4()),
                        question_id=question.id,
                        content=opt_data.content,
                        order=opt_data.order
                    )
                    db.add(option)
    
    db.commit()
    add_log("info", f"管理员 {current_user.username} 更新了问卷: {survey.title}")
    
    return {"message": "问卷更新成功"}


@router.delete("/admin/{survey_id}")
async def delete_survey(
    survey_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除问卷（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以删除问卷")
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    db.delete(survey)
    db.commit()
    add_log("info", f"管理员 {current_user.username} 删除了问卷: {survey.title}")
    
    return {"message": "问卷删除成功"}


@router.get("/admin/{survey_id}/statistics")
async def get_survey_statistics(
    survey_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取问卷统计（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看统计")
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    stats = {
        "survey_id": survey.id,
        "title": survey.title,
        "total_responses": survey.total_responses,
        "questions": []
    }
    
    for question in survey.questions:
        q_stat = {
            "id": question.id,
            "title": question.title,
            "question_type": question.question_type,
            "answer_count": len(question.answers)
        }
        
        if question.question_type == QuestionType.SINGLE_CHOICE.value:
            # 统计各选项选择次数
            option_stats = {}
            for opt in question.options:
                count = db.query(SurveyAnswer).filter(
                    SurveyAnswer.question_id == question.id,
                    SurveyAnswer.selected_option_id == opt.id
                ).count()
                option_stats[opt.content] = count
            q_stat["option_statistics"] = option_stats
            
        elif question.question_type == QuestionType.MULTIPLE_CHOICE.value:
            # 统计各选项选择次数
            option_stats = {}
            for opt in question.options:
                count = db.query(SurveyAnswer).filter(
                    SurveyAnswer.question_id == question.id,
                    SurveyAnswer.answer_data.contains({"option_ids": [opt.id]})
                ).count()
                option_stats[opt.content] = count
            q_stat["option_statistics"] = option_stats
            
        elif question.question_type == QuestionType.RATING.value:
            # 统计平均分
            answers = db.query(SurveyAnswer).filter(SurveyAnswer.question_id == question.id).all()
            if answers:
                total = sum(a.answer_data.get("value", 0) for a in answers)
                q_stat["average_rating"] = round(total / len(answers), 2)
                q_stat["rating_count"] = len(answers)
        
        stats["questions"].append(q_stat)
    
    return stats


# ========== 用户API ==========

@router.get("/list")
async def list_surveys(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取可填写的问卷列表（用户）"""
    now = datetime.utcnow()
    
    # 获取已发布的、在有效期内的问卷
    query = db.query(Survey).filter(Survey.status == SurveyStatus.PUBLISHED.value)
    
    surveys = query.order_by(desc(Survey.created_at)).all()
    available_surveys = []
    
    for s in surveys:
        # 检查时间有效性
        if s.start_time and s.start_time > now:
            continue
        if s.end_time and s.end_time < now:
            continue
        
        # 检查用户是否已填写
        has_submitted = False
        if current_user:
            existing = db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == s.id,
                SurveyResponse.user_id == current_user.id,
                SurveyResponse.is_submitted == True
            ).first()
            has_submitted = existing is not None
        
        available_surveys.append({
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "allow_anonymous": s.allow_anonymous,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "has_submitted": has_submitted,
            "question_count": len(s.questions)
        })
    
    return {"surveys": available_surveys}


@router.get("/{survey_id}")
async def get_survey(
    survey_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取问卷详情（用户）"""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    if survey.status != SurveyStatus.PUBLISHED.value:
        raise HTTPException(status_code=403, detail="问卷未发布")
    
    # 检查时间有效性
    now = datetime.utcnow()
    if survey.start_time and survey.start_time > now:
        raise HTTPException(status_code=403, detail="问卷尚未开始")
    if survey.end_time and survey.end_time < now:
        raise HTTPException(status_code=403, detail="问卷已结束")
    
    # 检查是否已填写
    has_submitted = False
    if current_user:
        existing = db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == current_user.id,
            SurveyResponse.is_submitted == True
        ).first()
        has_submitted = existing is not None
        
        if has_submitted and not survey.allow_multiple:
            raise HTTPException(status_code=403, detail="您已填写过此问卷")
    
    questions = []
    for q in sorted(survey.questions, key=lambda x: x.order):
        q_data = {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "question_type": q.question_type,
            "is_required": q.is_required,
            "order": q.order,
            "config": q.config
        }
        
        if q.question_type in [QuestionType.SINGLE_CHOICE.value, QuestionType.MULTIPLE_CHOICE.value]:
            q_data["options"] = [
                {"id": opt.id, "content": opt.content, "order": opt.order}
                for opt in sorted(q.options, key=lambda x: x.order)
            ]
        
        questions.append(q_data)
    
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "allow_anonymous": survey.allow_anonymous,
        "allow_multiple": survey.allow_multiple,
        "questions": questions,
        "has_submitted": has_submitted
    }


@router.post("/{survey_id}/submit")
async def submit_survey(
    request: Request,
    survey_id: str,
    data: SurveySubmit,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """提交问卷"""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    if survey.status != SurveyStatus.PUBLISHED.value:
        raise HTTPException(status_code=403, detail="问卷未发布")
    
    # 检查时间有效性
    now = datetime.utcnow()
    if survey.start_time and survey.start_time > now:
        raise HTTPException(status_code=403, detail="问卷尚未开始")
    if survey.end_time and survey.end_time < now:
        raise HTTPException(status_code=403, detail="问卷已结束")
    
    # 检查匿名权限
    if data.is_anonymous and not survey.allow_anonymous:
        raise HTTPException(status_code=403, detail="此问卷不允许匿名填写")
    
    # 获取用户IP地址（仅用于记录，不做限制）
    client_ip = request.client.host if request.client else "unknown"
    
    # 检查是否已填写（针对登录用户）
    if current_user:
        existing = db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == current_user.id,
            SurveyResponse.is_submitted == True
        ).first()
        
        if existing and not survey.allow_multiple:
            raise HTTPException(status_code=403, detail="您已填写过此问卷")
    
    # 创建填写记录
    response = SurveyResponse(
        id=str(uuid.uuid4()),
        survey_id=survey_id,
        user_id=current_user.id if current_user else None,
        user_ip=client_ip,
        is_anonymous=data.is_anonymous,
        is_submitted=True,
        submitted_at=now
    )
    db.add(response)
    
    # 保存答案
    for answer_data in data.answers:
        question = db.query(SurveyQuestion).filter(
            SurveyQuestion.id == answer_data.question_id,
            SurveyQuestion.survey_id == survey_id
        ).first()
        
        if not question:
            continue
        
        answer = SurveyAnswer(
            id=str(uuid.uuid4()),
            response_id=response.id,
            question_id=question.id
        )
        
        # 根据问题类型处理答案
        if question.question_type == QuestionType.SINGLE_CHOICE.value:
            option_id = answer_data.answer_data.get("option_id")
            answer.selected_option_id = option_id
            answer.answer_data = {
                "type": "single_choice",
                "option_id": option_id,
                "text": answer_data.answer_data.get("text", "")
            }
            
        elif question.question_type == QuestionType.MULTIPLE_CHOICE.value:
            option_ids = answer_data.answer_data.get("option_ids", [])
            answer.answer_data = {
                "type": "multiple_choice",
                "option_ids": option_ids,
                "texts": answer_data.answer_data.get("texts", [])
            }
            
        elif question.question_type == QuestionType.FILL_IN_BLANK.value:
            text = answer_data.answer_data.get("text", "")
            answer.answer_content = text
            answer.answer_data = {
                "type": "fill_in_blank",
                "text": text
            }
            
        elif question.question_type == QuestionType.RATING.value:
            value = answer_data.answer_data.get("value", 0)
            answer.answer_data = {
                "type": "rating",
                "value": value
            }
        
        db.add(answer)
    
    # 更新问卷统计
    survey.total_responses += 1
    
    db.commit()
    add_log("info", f"用户 {current_user.username if current_user else '匿名'} 提交了问卷: {survey.title}")
    
    return {"message": "问卷提交成功"}


@router.get("/my/responses")
async def get_my_responses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取我填写的问卷记录"""
    responses = db.query(SurveyResponse).filter(
        SurveyResponse.user_id == current_user.id,
        SurveyResponse.is_submitted == True
    ).order_by(desc(SurveyResponse.submitted_at)).all()
    
    result = []
    for r in responses:
        result.append({
            "id": r.id,
            "survey_id": r.survey_id,
            "survey_title": r.survey.title,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "is_anonymous": r.is_anonymous
        })
    
    return {"responses": result}


@router.get("/{survey_id}/statistics")
async def get_survey_public_statistics(
    survey_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取问卷统计（用户填写后可查看）"""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    # 检查用户是否已填写
    has_submitted = False
    if current_user:
        existing = db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == current_user.id,
            SurveyResponse.is_submitted == True
        ).first()
        has_submitted = existing is not None
    
    if not has_submitted:
        raise HTTPException(status_code=403, detail="请先填写问卷后再查看统计")
    
    stats = {
        "survey_id": survey.id,
        "title": survey.title,
        "total_responses": survey.total_responses,
        "questions": []
    }
    
    for question in sorted(survey.questions, key=lambda x: x.order):
        q_stat = {
            "id": question.id,
            "title": question.title,
            "question_type": question.question_type,
            "answer_count": len(question.answers)
        }
        
        if question.question_type == QuestionType.SINGLE_CHOICE.value:
            # 统计各选项选择次数
            option_stats = []
            total = 0
            for opt in sorted(question.options, key=lambda x: x.order):
                count = db.query(SurveyAnswer).filter(
                    SurveyAnswer.question_id == question.id,
                    SurveyAnswer.selected_option_id == opt.id
                ).count()
                total += count
                option_stats.append({
                    "id": opt.id,
                    "content": opt.content,
                    "count": count
                })
            
            # 计算百分比
            for opt_stat in option_stats:
                opt_stat["percentage"] = round(opt_stat["count"] / total * 100, 1) if total > 0 else 0
            
            q_stat["options"] = option_stats
            
        elif question.question_type == QuestionType.MULTIPLE_CHOICE.value:
            # 统计各选项选择次数
            option_stats = []
            total_answers = len(question.answers)
            for opt in sorted(question.options, key=lambda x: x.order):
                count = db.query(SurveyAnswer).filter(
                    SurveyAnswer.question_id == question.id,
                    SurveyAnswer.answer_data.contains({"option_ids": [opt.id]})
                ).count()
                option_stats.append({
                    "id": opt.id,
                    "content": opt.content,
                    "count": count,
                    "percentage": round(count / total_answers * 100, 1) if total_answers > 0 else 0
                })
            
            q_stat["options"] = option_stats
            
        elif question.question_type == QuestionType.RATING.value:
            # 统计平均分
            answers = db.query(SurveyAnswer).filter(SurveyAnswer.question_id == question.id).all()
            if answers:
                total = sum(a.answer_data.get("value", 0) for a in answers)
                q_stat["average_rating"] = round(total / len(answers), 2)
                q_stat["rating_count"] = len(answers)
                q_stat["max_rating"] = question.config.get("max_rating", 5)
        
        stats["questions"].append(q_stat)
    
    return stats


# ========== 管理员填写记录API ==========

@router.get("/admin/{survey_id}/responses")
async def get_survey_responses(
    survey_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取问卷填写记录（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看填写记录")
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    query = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id, SurveyResponse.is_submitted == True)
    total = query.count()
    responses = query.order_by(desc(SurveyResponse.submitted_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for r in responses:
        user_info = None
        if not r.is_anonymous and r.user:
            user_info = {
                "id": r.user.id,
                "username": r.user.username,
                "email": r.user.email
            }
        
        result.append({
            "id": r.id,
            "user": user_info,
            "is_anonymous": r.is_anonymous,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None
        })
    
    return {"responses": result, "total": total, "page": page, "page_size": page_size}


@router.get("/admin/response/{response_id}")
async def get_response_detail(
    response_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个回答详情（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看回答详情")
    
    response = db.query(SurveyResponse).filter(SurveyResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="回答记录不存在")
    
    # 获取问卷信息
    survey = response.survey
    
    # 获取用户信息
    user_info = None
    if not response.is_anonymous and response.user:
        user_info = {
            "id": response.user.id,
            "username": response.user.username,
            "email": response.user.email
        }
    
    # 获取问题和答案
    questions_data = []
    for question in sorted(survey.questions, key=lambda x: x.order):
        # 查找该问题的答案
        answer = db.query(SurveyAnswer).filter(
            SurveyAnswer.response_id == response_id,
            SurveyAnswer.question_id == question.id
        ).first()
        
        answer_display = None
        if answer:
            if question.question_type == QuestionType.SINGLE_CHOICE.value:
                if answer.selected_option_id:
                    option = db.query(SurveyOption).filter(SurveyOption.id == answer.selected_option_id).first()
                    answer_display = option.content if option else answer.answer_data.get("text", "")
            
            elif question.question_type == QuestionType.MULTIPLE_CHOICE.value:
                texts = answer.answer_data.get("texts", [])
                answer_display = "、".join(texts)
            
            elif question.question_type == QuestionType.FILL_IN_BLANK.value:
                answer_display = answer.answer_content or answer.answer_data.get("text", "")
            
            elif question.question_type == QuestionType.RATING.value:
                answer_display = f"{answer.answer_data.get('value', 0)} 分"
        
        questions_data.append({
            "id": question.id,
            "title": question.title,
            "question_type": question.question_type,
            "answer": answer_display
        })
    
    return {
        "id": response.id,
        "survey_title": survey.title,
        "user": user_info,
        "is_anonymous": response.is_anonymous,
        "submitted_at": response.submitted_at.isoformat() if response.submitted_at else None,
        "questions": questions_data
    }
