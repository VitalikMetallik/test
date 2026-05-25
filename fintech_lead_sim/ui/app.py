import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from typing import List

# Добавляем корень проекта в path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_core.orchestrator import GameOrchestrator
from game_core.models import TaskStatus, TaskType, Employee, Task

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(
    page_title="FinTech Lead Simulator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "FinTech Lead Simulator v2.0 | Created for Python 3.13"
    }
)

# --- КАСТОМНЫЙ CSS (СОВРЕМЕННЫЙ ДИЗАЙН) ---
st.markdown("""
<style>
    /* Основные переменные и шрифты */
    :root {
        --primary: #2563eb;
        --secondary: #7c3aed;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-card: #ffffff;
        --text-main: #1f2937;
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }

    /* Карточки */
    .stCard {
        background: var(--bg-card);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        border: 1px solid rgba(255,255,255,0.5);
    }
    .stCard:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    }

    /* Метрики */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #111827;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
    }

    /* Кнопки */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    /* Бейджи статусов */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-backlog { background: #e5e7eb; color: #374151; }
    .badge-progress { background: #dbeafe; color: #1e40af; }
    .badge-review { background: #fef3c7; color: #92400e; }
    .badge-done { background: #d1fae5; color: #065f46; }

    /* Анимации */
    @keyframes pulse-warning {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .alert-pulse {
        animation: pulse-warning 2s infinite;
    }

    /* Скроллбар */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)


# --- ИНИЦИАЛИЗАЦИЯ ---
@st.cache_resource
def get_orchestrator():
    return GameOrchestrator()


orch = get_orchestrator()

# Инициализация session_state
if 'notifications' not in st.session_state:
    st.session_state.notifications = []


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ UI ---

def show_toast_notifications():
    """Показывает всплывающие уведомления."""
    for msg in st.session_state.notifications:
        st.toast(msg, icon="🔔")
    st.session_state.notifications = []


def get_status_badge(status: str) -> str:
    badges = {
        "Backlog": "badge-backlog",
        "In Progress": "badge-progress",
        "Review": "badge-review",
        "Done": "badge-done",
        "Failed": "badge-danger"
    }
    cls = badges.get(status, "badge-backlog")
    return f'<span class="badge {cls}">{status}</span>'


def get_task_type_icon(t_type: str) -> str:
    icons = {
        "Feature": "✨",
        "Bug": "🐛",
        "TechDebt": "🔧",
        "Compliance": "🔒",
        "Incident": "🚨"
    }
    return icons.get(t_type, "📋")


# --- МОДАЛЬНЫЕ ОКНА (DIALOGS) ---

@st.dialog("🔍 Найм сотрудника", width="large")
def hire_dialog(candidates: List[Employee]):
    st.write("Выберите кандидата для найма:")
    cols = st.columns(len(candidates))
    for idx, cand in enumerate(candidates):
        with cols[idx]:
            st.markdown(f"""
            <div class="stCard">
                <h4>{cand.name}</h4>
                <p><b>Роль:</b> {cand.role.value}</p>
                <p><b>Скилл:</b> {cand.skill}/10</p>
                <p><b>Зарплата:</b> {cand.salary:,}₽</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Нанять", key=f"hire_{cand.id}"):
                if orch.hire_employee(cand):
                    st.session_state.notifications.append(f"✅ {cand.name} принят в команду!")
                    st.rerun()
                else:
                    st.error("❌ Недостаточно бюджета!")


@st.dialog("📋 Назначить задачу", width="medium")
def assign_dialog():
    state = orch.get_state()
    tasks = [t for t in state.tasks if t.status == TaskStatus.BACKLOG]
    emps = [e for e in state.employees if not e.is_busy]

    if not tasks:
        st.warning("Нет задач в бэклоге.")
        return
    if not emps:
        st.warning("Нет свободных сотрудников.")
        return

    with st.form("assign_form"):
        task_opts = {f"{get_task_type_icon(t.task_type.value)} {t.title}": t.id for t in tasks}
        emp_opts = {f"{e.name} ({e.role.value})": e.id for e in emps}

        sel_task_title = st.selectbox("Задача", options=list(task_opts.keys()))
        sel_emp_title = st.selectbox("Сотрудник", options=list(emp_opts.keys()))

        if st.form_submit_button("🚀 Назначить", type="primary"):
            success = orch.assign_task(task_opts[sel_task_title], emp_opts[sel_emp_title])
            if success:
                st.session_state.notifications.append("📋 Задача успешно назначена.")
                st.rerun()
            else:
                st.error("Ошибка назначения.")


@st.dialog("🗓 Провести встречу", width="small")
def meeting_dialog():
    st.write("Выберите тип встречи:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤝 1-on-1\n(5000₽, +Мораль)", use_container_width=True):
            msg = orch.start_meeting("1-on-1")
            st.session_state.notifications.append(msg)
            st.rerun()
    with col2:
        if st.button("🔧 Tech Review\n(2000₽, -Техдолг)", use_container_width=True):
            msg = orch.start_meeting("Tech Review")
            st.session_state.notifications.append(msg)
            st.rerun()


# --- ОСНОВНОЙ ИНТЕРФЕЙС ---

def render_sidebar():
    state = orch.get_state()

    with st.sidebar:
        st.title("💼 FinTech Lead")
        st.caption("Симулятор тимлида v2.0")
        st.divider()

        # Ключевые метрики
        st.markdown("### 📊 Показатели")
        st.metric("📅 День", state.day)
        st.metric("💰 Бюджет", f"{state.budget:,} ₽")

        # Прогресс-бары
        st.markdown("#### 📈 Состояние")
        st.progress(state.stakeholder_trust / 100, text=f"🤝 Доверие: {state.stakeholder_trust:.0f}%")
        st.progress(state.tech_debt / 100, text=f"💻 Техдолг: {state.tech_debt:.0f}%")
        st.progress(state.compliance_level / 100, text=f"🔒 Комплаенс: {state.compliance_level:.0f}%")

        st.divider()

        # Управление
        st.markdown("### 🎮 Управление")
        if st.button("▶️ Следующий день", type="primary", use_container_width=True):
            result = orch.tick()
            if result.get("events"):
                for evt in result["events"]:
                    st.session_state.notifications.append(evt)
            if result.get("errors"):
                st.error("💀 " + " ".join(result["errors"]))
                st.stop()
            st.rerun()

        if st.button("🔄 Новая игра", use_container_width=True):
            orch.reset_game()
            st.session_state.notifications.append("♻️ Игра перезапущена.")
            st.rerun()


def render_dashboard():
    state = orch.get_state()

    # Верхняя панель действий
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔍 Нанять сотрудников", use_container_width=True):
            hire_dialog(orch.get_candidates(3))
    with col2:
        if st.button("📋 Назначить задачу", use_container_width=True):
            assign_dialog()
    with col3:
        if st.button("🗓 Провести встречу", use_container_width=True):
            meeting_dialog()

    st.divider()

    # Сетка метрик команды
    st.markdown("### 👥 Состояние команды")
    if not state.employees:
        st.warning("Команда пуста! Срочно наймите сотрудников.")
    else:
        cols = st.columns(min(len(state.employees), 4))
        for idx, emp in enumerate(state.employees):
            with cols[idx % len(cols)]:
                morale_color = "🟢" if emp.morale > 60 else "🟡" if emp.morale > 30 else "🔴"
                energy_color = "🟢" if emp.energy > 60 else "🟡" if emp.energy > 30 else "🔴"

                st.markdown(f"""
                <div class="stCard">
                    <h4>{emp.name}</h4>
                    <p style="color:#6b7280; font-size:0.875rem;">{emp.role.value} • Skill: {emp.skill}</p>
                    <div style="margin: 1rem 0;">
                        <p>{morale_color} Мораль: {emp.morale:.0f}%</p>
                        <div style="background:#e5e7eb; border-radius:4px; height:6px; margin-bottom:0.5rem;">
                            <div style="background:#10b981; width:{emp.morale}%; height:6px; border-radius:4px;"></div>
                        </div>
                        <p>{energy_color} Энергия: {emp.energy:.0f}%</p>
                        <div style="background:#e5e7eb; border-radius:4px; height:6px;">
                            <div style="background:#3b82f6; width:{emp.energy}%; height:6px; border-radius:4px;"></div>
                        </div>
                    </div>
                    <p style="font-size:0.875rem; color:#6b7280;">💰 {emp.salary:,}₽/мес</p>
                    {'<p style="color:#ef4444; font-weight:600;">🔨 Занят задачей</p>' if emp.is_busy else '<p style="color:#10b981; font-weight:600;">✅ Свободен</p>'}
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Инциденты и алерты
    incidents = [t for t in state.tasks if
                 t.status != TaskStatus.DONE and t.task_type in [TaskType.INCIDENT, TaskType.COMPLIANCE]]
    if incidents:
        st.markdown("### 🚨 Активные инциденты")
        for inc in incidents:
            st.error(f"**{inc.title}** | Сложность: {inc.complexity} | Штраф: {inc.penalty}₽", icon="⚠️")


def render_backlog():
    state = orch.get_state()

    st.markdown("### 📋 Бэклог задач")

    # Фильтры
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.multiselect("Фильтр по статусу",
                                       options=[s.value for s in TaskStatus],
                                       default=[s.value for s in TaskStatus]
                                       )

    tasks_filtered = [t for t in state.tasks if t.status.value in filter_status]

    if not tasks_filtered:
        st.info("Задач не найдено.")
        return

    # Таблица задач
    for task in tasks_filtered:
        icon = get_task_type_icon(task.task_type.value)
        badge = get_status_badge(task.status.value)
        assigned = next((e.name for e in state.employees if e.id == task.assigned_to), "—")

        with st.expander(f"{icon} {task.title} {badge}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Сложность", task.complexity)
            c2.metric("Награда", f"{task.reward:,}₽")
            c3.metric("Прогресс", f"{task.progress:.0f}%")
            c4.metric("Исполнитель", assigned)

            if task.status == TaskStatus.IN_PROGRESS:
                st.progress(task.progress / 100)


def render_analytics():
    state = orch.get_state()

    st.markdown("### 📊 Аналитика")

    col1, col2 = st.columns(2)

    with col1:
        # Распределение задач по типам
        task_types = pd.Series([t.task_type.value for t in state.tasks]).value_counts()
        if not task_types.empty:
            fig = go.Figure(data=[go.Pie(labels=task_types.index, values=task_types.values, hole=.3)])
            fig.update_layout(title="Распределение задач", height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Навыки команды
        if state.employees:
            skills = {e.name: e.skill for e in state.employees}
            df_skills = pd.DataFrame(list(skills.items()), columns=['Сотрудник', 'Скилл'])
            fig = go.Figure(go.Bar(x=df_skills['Сотрудник'], y=df_skills['Скилл'], marker_color='#3b82f6'))
            fig.update_layout(title="Скиллы команды", height=300, margin=dict(l=0, r=0, t=30, b=0), yaxis_range=[0, 10])
            st.plotly_chart(fig, use_container_width=True)


def render_logs():
    state = orch.get_state()

    st.markdown("### 📜 Журнал событий")

    with st.container(height=400):
        for log in state.logs:
            st.markdown(f"`{log}`")


# --- ЗАПУСК ПРИЛОЖЕНИЯ ---

def main():
    render_sidebar()
    show_toast_notifications()

    # Вкладки
    tab_dash, tab_backlog, tab_analytics, tab_logs = st.tabs([
        "📊 Дашборд",
        "📋 Бэклог",
        "📈 Аналитика",
        "📜 Логи"
    ])

    with tab_dash:
        render_dashboard()

    with tab_backlog:
        render_backlog()

    with tab_analytics:
        render_analytics()

    with tab_logs:
        render_logs()


if __name__ == "__main__":
    main()