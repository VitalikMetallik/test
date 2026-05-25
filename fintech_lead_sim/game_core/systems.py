import random
from typing import List, Tuple
from .models import Employee, Task, Role, TaskType, TaskStatus, GameState


class EconomySystem:
    @staticmethod
    def calculate_payroll(state: GameState) -> int:
        return sum(emp.salary for emp in state.employees)

    @staticmethod
    def pay_salaries(state: GameState) -> bool:
        total = EconomySystem.calculate_payroll(state)
        if state.budget >= total:
            state.budget -= total
            state.add_log(f"Выплачены зарплаты: -{total} ₽")
            return True
        else:
            state.add_log("💀 КРИТИЧНО: Не хватило денег на зарплаты! Команда уходит.")
            state.employees.clear()
            return False


class DevelopmentSystem:
    @staticmethod
    def process_tasks(state: GameState) -> List[str]:
        events = []
        for task in state.tasks:
            if task.status == TaskStatus.IN_PROGRESS and task.assigned_to:
                emp = next((e for e in state.employees if e.id == task.assigned_to), None)
                if emp:
                    eff = emp.work(8.0)
                    progress_gain = eff * (10.0 / task.complexity) * random.uniform(0.8, 1.2)

                    # Влияние техдолга
                    if state.tech_debt > 50:
                        progress_gain *= 0.7
                        if random.random() < 0.1:
                            events.append(f"🐛 Баг в задаче {task.title} из-за техдолга!")

                    task.progress += progress_gain

                    if task.progress >= 100:
                        task.status = TaskStatus.REVIEW
                        emp.is_busy = False
                        emp.current_task_id = None
                        events.append(f"✅ Задача {task.title} готова к ревью.")

                        # Награда и риски
                        state.budget += task.reward
                        if task.task_type == TaskType.TECH_DEBT:
                            state.tech_debt = max(0, state.tech_debt - 5)
                            events.append("🔧 Техдолг уменьшен.")
                        elif task.task_type == TaskType.COMPLIANCE:
                            state.compliance_level = min(100, state.compliance_level + 2)
        return events

    @staticmethod
    def review_tasks(state: GameState):
        for task in state.tasks:
            if task.status == TaskStatus.REVIEW:
                # Автосимуляция ревью
                success = random.random() > 0.2
                if success:
                    task.status = TaskStatus.DONE
                    state.stakeholder_trust = min(100, state.stakeholder_trust + 1)
                    state.add_log(f"🎉 {task.title} принята стейкхолдерами.")
                else:
                    task.status = TaskStatus.IN_PROGRESS
                    task.progress = 80
                    state.add_log(f"🔄 {task.title} возвращена на доработку.")


class EventSystem:
    INCIDENTS = [
        ("🚨 Упала интеграция с ЦБ!", 20, 10, TaskType.INCIDENT),
        ("🔒 Аудит безопасности нашел уязвимость!", 15, 15, TaskType.COMPLIANCE),
        ("📉 Стейкхолдер требует срочный отчет!", 5, 5, TaskType.FEATURE),
        ("💾 Дедлок в базе данных!", 25, 10, TaskType.BUG),
    ]

    @staticmethod
    def generate_daily_events(state: GameState) -> List[str]:
        events = []

        # Случайный инцидент
        if random.random() < 0.2:
            title, complexity, penalty, t_type = random.choice(EventSystem.INCIDENTS)
            task = Task(title=title, task_type=t_type, complexity=complexity, penalty=penalty, reward=0)
            state.tasks.append(task)
            events.append(f"⚡ СОБЫТИЕ: {title}")
            state.stakeholder_trust = max(0, state.stakeholder_trust - 2)

        # Влияние морали
        for emp in state.employees:
            if emp.morale < 30 and random.random() < 0.1:
                events.append(f"😞 {emp.name} выгорел и взял отгул.")
                emp.energy = 0

            # Восстановление
            if not emp.is_busy:
                emp.rest(8.0)

        # Рост техдолга
        active_features = sum(
            1 for t in state.tasks if t.task_type == TaskType.FEATURE and t.status == TaskStatus.IN_PROGRESS)
        state.tech_debt = min(100, state.tech_debt + active_features * 0.5)

        return events


class HiringSystem:
    CANDIDATE_NAMES = ["Алексей", "Мария", "Дмитрий", "Елена", "Иван", "Ольга", "Сергей", "Анна"]

    @staticmethod
    def generate_candidate() -> Employee:
        role = random.choice(list(Role))
        skill = random.randint(3, 9)
        salary = skill * 10000 + (50000 if role == Role.SENIOR else 20000)
        name = random.choice(HiringSystem.CANDIDATE_NAMES)
        return Employee(name=f"{name} {random.randint(10, 99)}", role=role, skill=skill, salary=salary)