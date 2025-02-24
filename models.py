from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func

# 사용자 테이블
class User(Base):
    __tablename__ = "user"

    user_id = Column(String(255), primary_key=True)  # 사용자 ID
    user_pw = Column(String(255), nullable=False)  # 비밀번호
    username = Column(String(100), nullable=False)  # 사용자 이름
    site_id = Column(String(255), nullable=True)  # 안전신문고 ID
    site_pw = Column(String(255), nullable=True)  # 안전신문고 비밀번호
    phone = Column(String(11), nullable=False, unique=True)  # 전화번호
    email = Column(String(255), nullable=True, unique=True)  # 이메일

    detections = relationship("Detected", back_populates="user")
    reports = relationship("Report", back_populates="user")
    esg_score = relationship("ESG", back_populates="user")



# 검출 테이블
class Detected(Base):
    __tablename__ = "detected"

    detected_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    car_num = Column(String(255), nullable=False)
    d_video_path = Column(String(255), nullable=False)
    place = Column(String(255), nullable=False)
    violation = Column(String(255), nullable = False)
    time = Column(DateTime, nullable = True)

    user = relationship("User", back_populates="detections")
    reports = relationship("Report", back_populates="detected")

# 신고 테이블
class Report(Base):
    __tablename__ = "report"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    detected_id = Column(Integer, ForeignKey("detected.detected_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    report_status = Column(String(100), nullable=False, default="pending")
    report_violation = Column(Text, nullable=False)

    detected = relationship("Detected", back_populates="reports")
    user = relationship("User", back_populates="reports")

class Violation(Base):
    __tablename__ = "violation"
    
    violation_id = Column(Integer, primary_key=True, autoincrement=True)
    detected_id = Column(Integer, ForeignKey("detected.detected_id", ondelete="CASCADE"), nullable=False)
    violation = Column(Text, nullable=False)


class ESG(Base):
    __tablename__ = "esg"


    esg_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("report.report_id", ondelete="CASCADE"), nullable=False)
    esg_score = Column(DECIMAL(5, 2), nullable=False)
    rate = Column(String(200), nullable=True)  # 등급

    # 관계 설정
    user = relationship("User", back_populates="esg_score")


