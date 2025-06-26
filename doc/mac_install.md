# Подготовка окружения (macOS)

## 📦 Зависимости

- macOS с терминалом
- [Homebrew](https://brew.sh/) — менеджер пакетов
- Python ≥ 3.12 (опционально: 3.13, если нужен pre-release)
- pip (идёт в комплекте с Python)
- Виртуальное окружение `.venv`

---

## 🚀 Первый запуск

### 1. Установи Homebrew (если ещё не установлен)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Проверь:

```bash
brew --version
```

---

### 2. Установи Python

```bash
brew install python
```

Проверь:

```bash
python3 --version
pip3 --version
```

Ожидается:
```
Python 3.12.x
pip 24.x
```

> ❗️ Не используй системный `/usr/bin/python` — он устарел.

---

### 3. Создай виртуальное окружение

```bash
python3 -m venv .venv
```

Активируй его:

```bash
source .venv/bin/activate
```

Проверь:

```bash
which python
# → должно быть что-то вроде: /your/project/.venv/bin/python
```

---

### 4. Установи зависимости

Если есть `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🧪 Полезные команды

| Описание                     | Команда                   |
|-----------------------------|----------------------------|
| Активация venv              | `source .venv/bin/activate` |
| Деактивация venv            | `deactivate`               |
| Установка нового пакета     | `pip install <package>`    |
| Заморозка зависимостей      | `pip freeze > requirements.txt` |

---

## 🛠 Альтернатива: Python 3.13 (beta) через pyenv

```bash
brew install pyenv
pyenv install 3.13.0b1
pyenv global 3.13.0b1
python -m venv .venv
```

---

## 📁 Структура проекта

```text
.project-root/
├── .venv/               # виртуальное окружение
├── src/                 # основной код
├── requirements.txt     # зависимости
└── README.md            # ты здесь!
```
