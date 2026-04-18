import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import json

from . import models, schemas
from .database import engine, get_db

# 로컬 테스트 환경을 위해 Base 삭제를 주석 처리했습니다. Base.metadata.create_all은 서버 시작시 테이블을 동기화합니다.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Golf Swing Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 배포시에는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 1. 회원 가입 / 조회 (단순화)
@app.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        return db_user
    new_user = models.User(email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. 영상 업로드
@app.post("/upload", response_model=schemas.SwingResponse)
async def upload_video(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 유저 확인
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    new_swing = models.Swing(user_id=user_id, video_path=str(file_path))
    db.add(new_swing)
    db.commit()
    db.refresh(new_swing)

    # TODO: 비동기적으로 AI 포즈 추출 파이프라인 트리거 (현재는 간단히 더미 파이프라인 호출)
    from .ai.pose_extractor import process_video
    process_video(db, new_swing.id, str(file_path))

    return new_swing

# 3. 추출된 3D 포즈 데이터 조회 (Three.js 활용)
@app.get("/pose/{swing_id}", response_model=list[schemas.PoseResponse])
def get_pose(swing_id: int, db: Session = Depends(get_db)):
    poses = db.query(models.Pose).filter(models.Pose.swing_id == swing_id).order_by(models.Pose.frame_index).all()
    return poses

# 4. 스윙 분석 결과 요청
@app.post("/analyze", response_model=schemas.AnalysisResponse)
def run_analysis(swing_id: int, db: Session = Depends(get_db)):
    # 분석은 pose 데이터가 있을 때만 가능
    poses_exist = db.query(models.Pose).filter(models.Pose.swing_id == swing_id).first()
    if not poses_exist:
        raise HTTPException(status_code=400, detail="Pose data not found for this swing")
    
    from .ai.analyzer import analyze_swing
    analysis_result = analyze_swing(db, swing_id)
    return analysis_result

# 5. GPT 레슨 요청
@app.post("/lesson", response_model=schemas.LessonResponse)
def get_lesson(swing_id: int, db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.swing_id == swing_id).first()
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis data not found. Please analyze first.")

    from .ai.lesson_gen import generate_lesson
    lesson_obj = generate_lesson(db, swing_id, analysis.result_json)
    return lesson_obj
