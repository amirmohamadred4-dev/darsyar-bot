from datetime import datetime

from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Boolean,
    Date,
    Time,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DATABASE_URL


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL تنظیم نشده است.")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150))
    grade: Mapped[str] = mapped_column(
        String(30),
        default="یازدهم",
    )
    field: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    subject: Mapped[str] = mapped_column(String(100))
    field: Mapped[str] = mapped_column(String(30))


class UserTeacher(Base):
    __tablename__ = "user_teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE")
    )
    subject: Mapped[str] = mapped_column(String(100))

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "subject",
            name="uq_user_subject",
        ),
    )


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE")
    )
    subject: Mapped[str] = mapped_column(String(100))
    field: Mapped[str] = mapped_column(String(30))
    day_of_week: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[object] = mapped_column(Time)
    end_time: Mapped[object] = mapped_column(Time)
    title: Mapped[str] = mapped_column(
        String(200),
        default="",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        default="seed",
    )


class ClassRecord(Base):
    __tablename__ = "class_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE")
    )
    date: Mapped[object] = mapped_column(Date)

    status: Mapped[str] = mapped_column(
        String(20),
        default="unseen",
    )

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    start_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    followup_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "class_id",
            "date",
            name="uq_record",
        ),
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    reminder_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
    )

    start_reminder_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    nightly_report_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    nightly_report_hour: Mapped[int] = mapped_column(
        Integer,
        default=23,
    )

    nightly_report_minute: Mapped[int] = mapped_column(
        Integer,
        default=45,
    )

    last_report_date: Mapped[object | None] = mapped_column(
        Date,
        nullable=True,
    )


def init_db():
    Base.metadata.create_all(engine)


def session():
    return SessionLocal()
