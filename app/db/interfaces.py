from typing import Any, List, Optional
from sqlalchemy import delete
from sqlalchemy.future import select


class DatabaseInterface:

    @staticmethod
    async def get(db, table: Any, column: str, value: int | str) -> Optional[Any]:
        stmt = select(table).where(getattr(table, column) == value)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def filter(db, table: Any, column: str, value: int | str) -> Optional[Any]:
        stmt = select(table).where(getattr(table, column) == value)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_all(db, table: Any, skip: int = 0, limit: int = 20) -> List[Any]:
        stmt = select(table).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create(db, table: Any, data: dict) -> Optional[Any]:
        obj = table(**data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def update(db, table: Any, item_id: int, data: dict) -> Optional[Any]:
        stmt = select(table).where(table.id == item_id)
        result = await db.execute(stmt)
        obj = result.scalars().first()

        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            await db.commit()
            await db.refresh(obj)
        return obj

    @staticmethod
    async def delete(db, table: Any, col: str, value: int) -> None:
        await db.execute(delete(table).where(getattr(table, col) == value))
        await db.commit()

    @staticmethod
    async def get_or_create(db, table: Any, column: str, value: int | str, data: dict) -> Optional[Any]:
        result = await db.execute(select(table).where(getattr(table, column) == value))
        obj = result.scalars().first()

        if not obj:
            obj = table(**data)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)

        return obj
    
    @staticmethod
    async def update_or_create(db, table: Any, column: str, value: int | str, data: dict) -> Optional[Any]:
        result = await db.execute(select(table).where(getattr(table, column) == value))
        obj = result.scalars().first()

        if obj:
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            obj = table(**data)
            db.add(obj)

        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def get_merged(db, table1, table2, column, value) -> Optional[Any]:
        result = await db.execute(
            select(table1).join(table2).where(getattr(table2, column) == value)
        )
        return result.scalars().first()
