import subprocess
import sys
import os


def main():
    """Запускает Streamlit приложение."""
    script_path = os.path.join(os.path.dirname(__file__), 'ui', 'app.py')
    print(f"🚀 Запуск FinTech Lead Simulator...")
    print(f"📂 Путь к скрипту: {script_path}")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", script_path], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Игра остановлена пользователем.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска: {e}")


if __name__ == "__main__":
    main()