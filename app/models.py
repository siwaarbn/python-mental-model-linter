from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    # A worked example, elaborated in full sentences, shown in its own box
    # under the prompt -- deliberately kept separate from `prompt` rather
    # than inlined in the same paragraph, since mixing instruction and
    # example in one block of text made the task harder to read at a glance.
    example = Column(Text, nullable=False, default="")
    starter_code = Column(Text, nullable=False, default="")
    target_misconceptions = Column(String, nullable=False, default="")
    # One example test case per line, e.g. "greet_n_times('Al', 3) -> 'Hi Al, Hi Al, Hi Al'".
    # Shown to a student when their submission triggers no findings, so a clean
    # scan comes with something concrete to verify against rather than just a
    # bare "looks fine" message.
    example_tests = Column(Text, nullable=False, default="")

    submissions = relationship("Submission", back_populates="task")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    source_code = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    parse_error = Column(Text, nullable=True)

    user = relationship("User", back_populates="submissions")
    task = relationship("Task", back_populates="submissions")
    findings = relationship("Finding", back_populates="submission", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)

    rule_id = Column(String, nullable=False)
    misconception_id = Column(String, nullable=False)
    misconception_name = Column(String, nullable=False)
    severity = Column(Integer, nullable=False)
    line = Column(Integer, nullable=True)
    column = Column(Integer, nullable=True)
    confidence = Column(String, nullable=True)

    layer1_observation = Column(Text, nullable=False)
    layer2_conceptual_explanation = Column(Text, nullable=False)
    layer3_mental_model_correction = Column(Text, nullable=False)
    layer4_reflection_prompt = Column(Text, nullable=False)

    submission = relationship("Submission", back_populates="findings")