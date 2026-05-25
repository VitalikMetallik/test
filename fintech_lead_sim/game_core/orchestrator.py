from typing import List, Optional, Dict
from .models import GameState, Employee, Task, TaskStatus, Role, TaskType
from .systems import EconomySystem, DevelopmentSystem, EventSystem, HiringSystem
from .database import DatabaseManager


class GameOrchestrator:
    def __init__(self, db_path: str = "game_save.db"):
        self.db = DatabaseManager(db_path)
        self.state = self.db.load_game()
        if not self.state:
            self.state = GameState()
            self._init_start_team()
            self.state.add_log("🚀 Игра началась! Вы тимлид в финтехе.")

    def _init_start_team(self):
        self.state.employees = [
            Employee(name="Алексей Dev", role=Role.MIDDLE, skill=6, salary=80000),
            Employee(name="Мария QA", role=Role.QA, skill=5, salary=60000),
        ]
        self.state.tasks = [
            Task(title="Реализовать API платежей", task_type=TaskType.FEATURE, complexity=7, reward=50000),
            Task(title="Покрыть тестами ядро", task_type=TaskType.TECH_DEBT, complexity=4, reward=10000),
        ]

    def tick(self) -> Dict[str, List[str]]:
        """Продвинуть симуляцию на 1 день."""
        results = {"events": [], "errors": []}

        # 1. Экономика
        if self.state.day % 7 == 0:
            if not EconomySystem.pay_salaries(self.state):
                results["errors"].append("Game Over: Нет денег.")
                return results

        # 2. События
        results["events"].extend(EventSystem.generate_daily_events(self.state))

        # 3. Разработка
        dev_events = DevelopmentSystem.process_tasks(self.state)
        results["events"].extend(dev_events)
        DevelopmentSystem.review_tasks(self.state)

        # 4. Обновление состояния
        self.state.day += 1

        # Проверка условий поражения
        if self.state.stakeholder_trust <= 0:
            results["errors"].append("Game Over: Стейкхолдеры потеряли доверие.")
        if not self.state.employees:
            results["errors"].append("Game Over: Команда разбежалась.")

        for msg in results["events"]:
            self.state.add_log(msg)

        self.db.save_game(self.state)
        return results

    def hire_employee(self, emp: Employee) -> bool:
        if self.state.budget >= emp.salary:
            self.state.employees.append(emp)
            self.state.add_log(f"👤 Нанят {emp.name} ({emp.role.value}).")
            self.db.save_game(self.state)
            return True
        return False

    def assign_task(self, task_id: str, emp_id: str) -> bool:
        task = next((t for t in self.state.tasks if t.id == task_id), None)
        emp = next((e for e in self.state.employees if e.id == emp_id), None)

        if task and emp and not emp.is_busy and task.status == TaskStatus.BACKLOG:
            task.status = TaskStatus.IN_PROGRESS
            task.assigned_to = emp_id
            emp.is_busy = True
            emp.current_task_id = task_id
            self.state.add_log(f"📋 {emp.name} начал задачу {task.title}.")
            self.db.save_game(self.state)
            return True
        return False

    def start_meeting(self, meeting_type: str) -> str:
        cost = 0
        effect = ""
        if meeting_type == "1-on-1":
            cost = 5000
            for emp in self.state.employees:
                emp.morale = min(100, emp.morale + 10)
            effect = "Мораль команды повышена."
        elif meeting_type == "Tech Review":
            cost = 2000
            self.state.tech_debt = max(0, self.state.tech_debt - 3)
            effect = "Техдолг проанализирован."

        if self.state.budget >= cost:
            self.state.budget -= cost
            self.state.add_log(f"🗓 {meeting_type}: {effect}")
            self.db.save_game(self.state)
            return f"Успех: {effect}"
        return "Недостаточно бюджета."

    def get_candidates(self, count: int = 3) -> List[Employee]:
        return [HiringSystem.generate_candidate() for _ in range(count)]

    def get_state(self) -> GameState:
        return self.state

    def reset_game(self):
        self.state = GameState()
        self._init_start_team()
        self.state.add_log("♻️ Игра перезапущена.")
        self.db.save_game(self.state)