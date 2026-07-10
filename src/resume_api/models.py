"""Pydantic models for every resume entity — see
docs/projects/resume-api/design.md (operations repo) for the domain model.
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class EmploymentType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"
    self_employed = "self-employed"


class SkillCategory(str, Enum):
    language = "language"
    framework = "framework"
    tool = "tool"
    soft_skill = "soft-skill"


class Proficiency(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class CertificationType(str, Enum):
    professional = "professional"
    personal = "personal"


class GoalCategory(str, Enum):
    career = "career"
    personal = "personal"
    learning = "learning"


class GoalStatus(str, Enum):
    active = "active"
    achieved = "achieved"
    abandoned = "abandoned"


class Profile(BaseModel):
    name: str
    headline: str | None = None
    summary: str | None = None
    location: str | None = None
    email: str | None = None
    links: dict[str, str] = Field(default_factory=dict)
    goals_summary: str | None = None


class Experience(BaseModel):
    organization: str
    title: str
    location: str | None = None
    employment_type: EmploymentType | None = None
    start_date: date
    end_date: date | None = None
    responsibilities: list[str] = Field(default_factory=list)
    accomplishments: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str | None = None
    location: str | None = None
    start_date: date
    end_date: date | None = None
    gpa: str | None = None
    honors: str | None = None
    activities: str | None = None


class Skill(BaseModel):
    name: str
    category: SkillCategory
    proficiency: Proficiency | None = None
    years_experience: float | None = None


class Certification(BaseModel):
    name: str
    issuing_organization: str
    issue_date: date
    expiration_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    type: CertificationType = CertificationType.professional


class Hobby(BaseModel):
    name: str
    description: str | None = None


class Goal(BaseModel):
    description: str
    category: GoalCategory
    target_date: date | None = None
    status: GoalStatus = GoalStatus.active
