from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger(__name__)

engine = create_engine(
    settings.database_url,
    future=True,
    echo=settings.app_debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db.base import Base
    # 导入模型，确保 metadata 已注册
    from app.modules.analysis import models as _analysis_models  # noqa: F401
    from app.modules.alert import models as _alert_models  # noqa: F401
    from app.modules.knowledge import models as _knowledge_models  # noqa: F401
    from app.modules.recommendation import models as _recommendation_models  # noqa: F401
    from app.modules.propaganda import models as _propaganda_models  # noqa: F401
    from app.modules.support_prosecution import models as _support_prosecution_models  # noqa: F401
    from app.modules.workflow import models as _workflow_models  # noqa: F401

    logger.info('creating database tables...')
    Base.metadata.create_all(bind=engine)
    logger.info('database tables ready')
