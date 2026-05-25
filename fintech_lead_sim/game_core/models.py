from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid
from datetime import datetime


class Role(Enum):
    JUNIOR = "Junior"
    MIDDLE = "Middle"
    SENIOR = "Senior"
    QA = "QA"
    DEVOPS = "DevOps"


class TaskType(Enum):
    FEATURE = "Feature"
    BUG = "Bug"
    TECH_DEBT = "TechDebt"
    COMPLIANCE = "Compliance"
    INCIDENT = "Incident"


class TaskStatus(Enum):
    BACKLOG = "Backlog"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    DONE = "Done"
    FAILED = "Failed"


@dataclass
class Employee:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Anonymous"
    role: Role = Role.JUNIOR
    skill: int = 5  # 1-10
    morale: float = 80.0  # 0-100
    energy: float = 100.0  # 0-100
    salary: int = 50000
    is_busy: bool = False
    current_task_id: Optional[str] = None

    def work(self, hours: float) -> float:
        """Возвращает эффективность работы."""
        if self.energy <= 0:
            return 0.0
        eff = (self.skill / 10.0) * (self.morale / 100.0) * (self.energy / 100.0)
        self.energy = max(0, self.energy - hours * 5)
        self.morale = max(0, min(100, self.morale - hours * 0.5))
        return eff

    def rest(self, hours: float):
        self.energy = min(100, self.energy + hours * 10)
        self.morale = min(100, self.morale + hours * 2)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'role': self.role.value,
            'skill': self.skill, 'morale': self.morale, 'energy': self.energy,
            'salary': self.salary, 'is_busy': self.is_busy, 'current_task_id': self.current_task_id
        }


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = "New Task"
    task_type: TaskType = TaskType.FEATURE
    complexity: int = 5  # 1-10
    progress: float = 0.0
    status: TaskStatus = TaskStatus.BACKLOG
    assigned_to: Optional[str] = None
    deadline: Optional[int] = None  # Days
    reward: int = 0
    penalty: int = 0

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'task_type': self.task_type.value,
            'complexity': self.complexity, 'progress': self.progress,
            'status': self.status.value, 'assigned_to': self.assigned_to,
            'deadline': self.deadline, 'reward': self.reward, 'penalty': self.penalty
        }


@dataclass
class GameState:
    day: int = 1
    budget: int = 1000000
    tech_debt: float = 0.0  # 0-100
    stakeholder_trust: float = 80.0  # 0-100
    compliance_level: float = 90.0  # 0-100
    employees: list = field(default_factory=list)
    tasks: list = field(default_factory=list)
    logs: list = field(default_factory=list)

    def add_log(self, message: str):
        timestamp = f"День {self.day}"
        self.logs.insert(0, f"[{timestamp}] {message}")
        if len(self.logs) > 50:
            self.logs.pop()