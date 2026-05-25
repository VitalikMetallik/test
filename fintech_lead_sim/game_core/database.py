import sqlite3
import json
from typing import Optional
from .models import GameState, Employee, Task, Role, TaskType, TaskStatus


class DatabaseManager:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def save_game(self, state: GameState):
        data = {
            'day': state.day, 'budget': state.budget, 'tech_debt': state.tech_debt,
            'stakeholder_trust': state.stakeholder_trust, 'compliance_level': state.compliance_level,
            'employees': [e.to_dict() for e in state.employees],
            'tasks': [t.to_dict() for t in state.tasks],
            'logs': state.logs
        }
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM game_state')
        cursor.execute('INSERT INTO game_state (id, data) VALUES (1, ?)', (json.dumps(data),))
        self.conn.commit()

    def load_game(self) -> Optional[GameState]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT data FROM game_state WHERE id = 1')
        row = cursor.fetchone()
        if not row:
            return None

        data = json.loads(row[0])
        state = GameState(
            day=data['day'], budget=data['budget'], tech_debt=data['tech_debt'],
            stakeholder_trust=data['stakeholder_trust'], compliance_level=data['compliance_level'],
            logs=data.get('logs', [])
        )
        for e in data['employees']:
            state.employees.append(Employee(
                id=e['id'], name=e['name'], role=Role(e['role']), skill=e['skill'],
                morale=e['morale'], energy=e['energy'], salary=e['salary'],
                is_busy=e['is_busy'], current_task_id=e['current_task_id']
            ))
        for t in data['tasks']:
            state.tasks.append(Task(
                id=t['id'], title=t['title'], task_type=TaskType(t['task_type']),
                complexity=t['complexity'], progress=t['progress'],
                status=TaskStatus(t['status']), assigned_to=t['assigned_to'],
                deadline=t['deadline'], reward=t['reward'], penalty=t['penalty']
            ))
        return state