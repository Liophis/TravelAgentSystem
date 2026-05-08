"""Diary Service - 处理旅游日记相关的业务逻辑"""

from sqlalchemy.orm import Session

from app.db import crud
from app.models.diary import TravelDiarySchema


class DiaryService:
    """处理日记管理、全文检索、压缩等"""

    def __init__(self):
        pass

    def create_diary(
        self, db: Session, user_id: int, title: str, content: str, poi_id: int = None
    ) -> TravelDiarySchema:
        """创建新的旅游日记"""
        diary = crud.create_diary(db, user_id, title, content, poi_id)
        return TravelDiarySchema(
            id=diary.id,
            user_id=diary.user_id,
            title=diary.title,
            content=diary.content,
            poi_id=diary.poi_id,
            created_at=diary.created_at,
            updated_at=diary.updated_at,
        )

    def get_user_diaries(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[TravelDiarySchema]:
        """获取用户的所有日记"""
        diaries = crud.get_diary_by_user(db, user_id, skip, limit)
        return [
            TravelDiarySchema(
                id=diary.id,
                user_id=diary.user_id,
                title=diary.title,
                content=diary.content,
                poi_id=diary.poi_id,
                created_at=diary.created_at,
                updated_at=diary.updated_at,
            )
            for diary in diaries
        ]

    def search_diary_by_keyword(self, db: Session, user_id: int, keyword: str) -> list[TravelDiarySchema]:
        """在用户日记中搜索关键词（后续实现全文检索）"""
        diaries = crud.get_diary_by_user(db, user_id, skip=0, limit=10000)

        # 简单的关键词匹配，后续可实现倒排索引
        results = [
            TravelDiarySchema(
                id=diary.id,
                user_id=diary.user_id,
                title=diary.title,
                content=diary.content,
                poi_id=diary.poi_id,
                created_at=diary.created_at,
                updated_at=diary.updated_at,
            )
            for diary in diaries
            if keyword.lower() in diary.content.lower() or keyword.lower() in diary.title.lower()
        ]
        return results
