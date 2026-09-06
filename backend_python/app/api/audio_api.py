"""
音频上传 API 路由（app/api/audio_api.py）

架构 §9.4 契约：`POST /audio/upload`（复用 Dio 上传链路）。

    POST /audio/upload    multipart 字段 audioFile → 落盘 → 建 interview 记录
    返回：{status, data: {interview_id, id, title, status, created_at}}

前端 upload 后随即调 POST /interview/{id}/analyze 触发复盘；进度经 WS 推送。
"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile, File
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.entities import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])


class AudioUploadOut(BaseModel):
    interview_id: int
    id: int
    title: str = ""
    status: str = "PENDING"
    created_at: str = ""


@router.post("/upload", response_model=AudioUploadOut)
async def upload_audio(
    request: Request,
    user: User = Depends(get_current_user),
    audioFile: UploadFile = File(...),
):
    """接收录音文件：存到 audio_storage_path，建立待分析的面试记录。"""
    db = request.app.state.database

    audio_dir = Path(settings.audio_storage_path)
    audio_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(audioFile.filename or "recording.wav").suffix or ".wav"
    dest = audio_dir / f"{uuid.uuid4().hex}{suffix}"
    content = await audioFile.read()
    dest.write_bytes(content)
    logger.info("保存音频: %s (%d bytes)", dest, len(content))

    title = Path(audioFile.filename or "").stem or "面试录音"
    interview_id = db.create_interview(user.id, title, str(dest))
    iv = db.get_interview(interview_id)
    return AudioUploadOut(
        interview_id=iv.id, id=iv.id, title=iv.title,
        status=iv.status, created_at=iv.created_at,
    )