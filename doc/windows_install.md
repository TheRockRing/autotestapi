# 🪟 Установка и запуск проекта на Windows

Инструкция по первичной настройке Python-проекта и запуску тестов в окружении Windows.

---

## 📦 Необходимое ПО

- Windows 10/11
- Python ≥ 3.12 (включая pip)
- Git (опционально)
- Виртуальное окружение `.venv`

---

## 🔧 Шаги установки

### 1. Установи Python

- Перейди на [https://www.python.org/downloads/](https://www.python.org/downloads/)
- Скачай последнюю стабильную версию (например, 3.12.x)
- ✅ Обязательно **поставь галочку** `Add Python to PATH` при установке

После установки проверь:

```cmd
python --version
pip --version
```

---

### 2. Создай виртуальное окружение

Открой `cmd` или `PowerShell` в корне проекта:

```cmd
python -m venv .venv
```

Активируй окружение:

```cmd
.venv\Scripts\activate
```

---

### 3. Установи зависимости

Если есть `requirements.txt`:

```cmd
pip install -r requirements.txt
```

---

## ✅ Проверка

После активации окружения:

```cmd
where python
where pip
```

Они должны указывать на `.venv\Scripts\python.exe` и `pip.exe`.

---

## 🧪 Запуск тестов

```cmd
pytest
```

(если проект использует `pytest`)

---

## 📁 Структура проекта

```text
.project-root/
├── .venv/               # виртуальное окружение
├── features/            # feature-файлы тестов
├── requirements.txt     # зависимости
└── README.md
```
