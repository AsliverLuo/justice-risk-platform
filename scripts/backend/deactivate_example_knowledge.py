from __future__ import annotations

from sqlalchemy import text

from app.db.session import SessionLocal


SQL = """
UPDATE legal_knowledge
SET status = 'inactive'
WHERE article_no LIKE '示例-%' OR source_type = 'example'
"""


def main() -> None:
    with SessionLocal() as db:
        result = db.execute(text(SQL))
        db.commit()
        print(f'inactivated rows: {result.rowcount}')


if __name__ == '__main__':
    main()
