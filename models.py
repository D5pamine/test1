from sqlalchemy import Column, Integer, String, ForeignKey, Text, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import UniqueConstraint

class Test(Base):
    __tablename__ = "test"
    test_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False)

# 사용자 테이블
class User(Base):
    __tablename__ = "user"
    user_id = Column(String(255), primary_key=True)
    user_pw = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False)
    site_id = Column(String(255), nullable=True)  # 데이터베이스와 맞추려면 수정 필요
    site_pw = Column(String(255), nullable=True)  # 데이터베이스와 맞추려면 수정 필요
    phone = Column(String(11), nullable=False, unique=True)
    email = Column(String(255), nullable=True)  # 데이터베이스와 맞추려면 수정 필요

    detections = relationship("Detected", back_populates="user", cascade="all, delete")
    reports = relationship("Report", back_populates="user", cascade="all, delete")
    esg_scores = relationship("ESG", back_populates="user", cascade="all, delete")

# 검출(Detected) 테이블
class Detected(Base):
    __tablename__ = "detected"
    detected_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    car_num = Column(String(255), nullable=False)
    d_video_path = Column(String(255), nullable=False)
    place = Column(String(255), nullable=False)
    violation = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="detections")
    report = relationship("Report", back_populates="detected", uselist=False)

# 신고(Report) 테이블
class Report(Base):
    __tablename__ = "report"
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    detected_id = Column(Integer, ForeignKey("detected.detected_id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(String(255), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)  # 데이터베이스와 맞추려면 nullable=False로 수정 필요
    report_result = Column(String(100), nullable=False, default="pending")
    report_violation = Column(Text, nullable=False)

    detected = relationship("Detected", back_populates="report", uselist=False)
    user = relationship("User", back_populates="reports")
    esg = relationship("ESG", back_populates="report", cascade="all, delete")

# 위반 사항 기록 테이블
class Violation(Base):
    __tablename__ = "violation"
    violation_id = Column(Integer, primary_key=True, autoincrement=True)
    detected_id = Column(Integer, ForeignKey("detected.detected_id", ondelete="CASCADE"), nullable=False)
    violation = Column(Text, nullable=False)

# ESG 점수 테이블
class ESG(Base):
    __tablename__ = "esg"
    esg_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("report.report_id", ondelete="CASCADE"), nullable=False)
    esg_score = Column(DECIMAL(5, 2), nullable=False)
    rate = Column(String(20), nullable=False)  # 데이터베이스와 맞춤

    user = relationship("User", back_populates="esg_scores")
    report = relationship("Report", back_populates="esg")