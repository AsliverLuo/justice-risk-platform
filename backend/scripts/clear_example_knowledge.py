from __future__ import annotations

from sqlalchemy import text

from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as db:
        result = db.execute(text("DELETE FROM legal_knowledge WHERE source_type = 'example' OR article_no LIKE '示例-%'"))
        db.commit()
        print(f"deleted rows: {result.rowcount}")


if __name__ == "__main__":
    main()
