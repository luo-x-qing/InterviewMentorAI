"""
业务数据库（app/core/database.py）

v3.1 全 Agent 架构的业务库：user / interview / coach_session /
coach_session_question / user_profile。

深模块设计：内部封装全部 SQLite 连接、建表、兼容补列与实体 CRUD，
对外暴露薄接口（get_conn / execute / 各实体读写方法）。

与向量库（app/core/vector_db.py）共用 data/interview.db 单文件，
此处只负责业务表（rag_* 表由向量库管理），互不冲突、可安全共存。
"""
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Iterable, List, Optional

from app.core.config import settings
from app.models.entities import (
    CoachAnswerRecord,
    CoachSession,
    CoachSessionStatus,
    Interview,
    InterviewStatus,
    User,
    UserProfile,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    """统一时间戳格式"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Database:
    """业务库：SQLite（个人模式），原生 sqlite3，可无缝升级 MySQL"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path if db_path is not None else settings.sqlite_db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_tables()
        self._migrate()

    # ── 内建表 ────────────────────────────────────────

    def _init_tables(self):
        """建业务表（幂等）"""
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            nickname TEXT DEFAULT '',
            hashed_password TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT '',
            audio_file_path TEXT DEFAULT '',
            status TEXT DEFAULT 'PENDING',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            final_report TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS coach_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            mode TEXT DEFAULT 'TEXT',
            status TEXT DEFAULT 'IDLE',
            difficulty TEXT DEFAULT 'MEDIUM',
            question_index INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS coach_session_question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_no TEXT DEFAULT '',
            title TEXT DEFAULT '',
            answer TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            level TEXT DEFAULT 'WEAK',
            knowledge_points TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            strengths TEXT DEFAULT '[]',
            weaknesses TEXT DEFAULT '[]',
            mastery TEXT DEFAULT '{}',
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
        """)

    def _migrate(self):
        """兼容旧库：为已存在但缺列的表补列（对齐 vector_db 的补列策略）"""
        expected = {
            "interviews": ["final_report"],
        }
        for table, cols in expected.items():
            existing = [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
            for col in cols:
                if col not in existing:
                    self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT ''")
        self.conn.commit()

    # ── 薄接口 ────────────────────────────────────────

    def get_conn(self) -> sqlite3.Connection:
        return self.conn

    def execute(self, sql: str, params: Iterable[Any] = ()):
        """执行写语句（提交）"""
        cur = self.conn.execute(sql, tuple(params))
        self.conn.commit()
        return cur

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        return self.conn.execute(sql, tuple(params)).fetchone()

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> List[sqlite3.Row]:
        return self.conn.execute(sql, tuple(params)).fetchall()

    # ── 用户 ──────────────────────────────────────────

    def create_user(self, phone: str, hashed_password: str, nickname: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO users (phone, nickname, hashed_password) VALUES (?, ?, ?)",
            (phone, nickname, hashed_password),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_user_by_phone(self, phone: str) -> Optional[User]:
        row = self.conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
        return self._user_from_row(row)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        row = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._user_from_row(row)

    @staticmethod
    def _user_from_row(row) -> Optional[User]:
        if row is None:
            return None
        return User(
            id=row["id"], phone=row["phone"], nickname=row["nickname"],
            hashed_password=row["hashed_password"], created_at=row["created_at"],
        )

    # ── 面试 ──────────────────────────────────────────

    def create_interview(self, user_id: int, title: str, audio_file_path: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO interviews (user_id, title, audio_file_path) VALUES (?, ?, ?)",
            (user_id, title, audio_file_path),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_interview(self, interview_id: int) -> Optional[Interview]:
        row = self.conn.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,)).fetchone()
        if row is None:
            return None
        return Interview(
            id=row["id"], user_id=row["user_id"], title=row["title"],
            audio_file_path=row["audio_file_path"], status=row["status"],
            created_at=row["created_at"], final_report=row["final_report"] or "",
        )

    def list_interviews(self, user_id: int) -> List[Interview]:
        rows = self.conn.execute(
            "SELECT * FROM interviews WHERE user_id = ? ORDER BY id DESC", (user_id,),
        ).fetchall()
        return [Interview(
            id=r["id"], user_id=r["user_id"], title=r["title"],
            audio_file_path=r["audio_file_path"], status=r["status"],
            created_at=r["created_at"], final_report=r["final_report"] or "",
        ) for r in rows]

    def update_interview_status(self, interview_id: int, status: str, final_report: str = "") -> None:
        self.conn.execute(
            "UPDATE interviews SET status = ?, final_report = ? WHERE id = ?",
            (status, final_report, interview_id),
        )
        self.conn.commit()

    # ── Coach 会话 ────────────────────────────────────

    def create_coach_session(self, user_id: int, mode: str = "TEXT", difficulty: str = "MEDIUM") -> CoachSession:
        session_id = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO coach_sessions (session_id, user_id, mode, status, difficulty) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, mode, CoachSessionStatus.IDLE.value, difficulty),
        )
        self.conn.commit()
        return self.get_coach_session(session_id)

    def get_coach_session(self, session_id: str) -> Optional[CoachSession]:
        row = self.conn.execute(
            "SELECT * FROM coach_sessions WHERE session_id = ?", (session_id,),
        ).fetchone()
        if row is None:
            return None
        return CoachSession(
            id=row["session_id"], user_id=row["user_id"], mode=row["mode"],
            status=row["status"], difficulty=row["difficulty"],
            question_index=row["question_index"], correct_count=row["correct_count"],
            total_count=row["total_count"], created_at=row["created_at"],
        )

    def update_coach_session(self, session: CoachSession) -> None:
        self.conn.execute(
            "UPDATE coach_sessions SET status=?, difficulty=?, question_index=?, "
            "correct_count=?, total_count=? WHERE session_id=?",
            (session.status, session.difficulty, session.question_index,
             session.correct_count, session.total_count, session.id),
        )
        self.conn.commit()

    def add_answer_record(self, rec: CoachAnswerRecord) -> None:
        self.conn.execute(
            "INSERT INTO coach_session_question (session_id, question_no, title, answer, "
            "score, level, knowledge_points, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (rec.session_id, rec.question_no, rec.title, rec.answer, rec.score,
             rec.level, rec.knowledge_points, _now()),
        )
        self.conn.commit()

    def list_answer_records(self, session_id: str) -> List[CoachAnswerRecord]:
        rows = self.conn.execute(
            "SELECT * FROM coach_session_question WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [CoachAnswerRecord(
            session_id=r["session_id"], question_no=r["question_no"], title=r["title"],
            answer=r["answer"], score=r["score"], level=r["level"],
            knowledge_points=r["knowledge_points"], created_at=r["created_at"],
        ) for r in rows]

    # ── 画像 ──────────────────────────────────────────

    def save_profile(self, profile: UserProfile) -> None:
        import json
        self.conn.execute(
            "INSERT INTO user_profile (user_id, strengths, weaknesses, mastery, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET strengths=excluded.strengths, "
            "weaknesses=excluded.weaknesses, mastery=excluded.mastery, updated_at=excluded.updated_at",
            (profile.user_id, json.dumps(profile.strengths, ensure_ascii=False),
             json.dumps(profile.weaknesses, ensure_ascii=False),
             json.dumps(profile.mastery, ensure_ascii=False), _now()),
        )
        self.conn.commit()

    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        import json
        row = self.conn.execute(
            "SELECT * FROM user_profile WHERE user_id = ?", (user_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            strengths = json.loads(row["strengths"] or "[]")
            weaknesses = json.loads(row["weaknesses"] or "[]")
            mastery = json.loads(row["mastery"] or "{}")
        except json.JSONDecodeError:
            strengths, weaknesses, mastery = [], [], {}
        return UserProfile(
            user_id=row["user_id"], strengths=strengths,
            weaknesses=weaknesses, mastery=mastery, updated_at=row["updated_at"],
        )

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None