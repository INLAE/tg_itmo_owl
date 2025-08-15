# domain.py
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Program:
    code: str
    name: str
    url: str
    plan_url: Optional[str] = None
    about_html: Optional[str] = None
    faq_text: Optional[str] = None

@dataclass
class Course:
    program_code: str
    name: str
    semester: Optional[int] = None
    type: str = "core"  # core | elective
    hours: Optional[int] = None
    credits: Optional[float] = None
    raw: Optional[str] = None
    tags: List[str] = field(default_factory=list)