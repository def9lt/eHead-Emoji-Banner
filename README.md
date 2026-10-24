<div align="center">

# 🎨 Telegram Emoji Pack Banner Generator

**Асинхронный Telegram-бот на Python (aiogram 3.x + Pillow + Lottie) для автоматического создания стильных превью-баннеров эмодзи-паков в высоком разрешении (1920×1200).**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg?logo=telegram)](https://github.com/aiogram/aiogram)
[![Pillow](https://img.shields.io/badge/Pillow-10.0+-green.svg)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author: Lux](https://img.shields.io/badge/Author-Lux-ff69b4.svg)](https://t.me/photoshopgame)

[Возможности](#-возможности) • [Установка](#-установка-и-запуск) • [Зависимости](#-системные-зависимости-linux) • [Архитектура](#-структура-проекта) • [Автор](#-автор)

</div>

---

## ✨ Возможности

- 🚀 **Парсинг ссылок любого формата**: бот принимает как прямые ссылки (`https://t.me/addemoji/<pack>`, `https://t.me/addstickers/<pack>`, `tg://addemoji?set=...`), так и просто короткое имя пака.
- ⚡️ **Умный рендеринг векторных .TGS**: распаковывает gzip-архивы Lottie, рендерит первый кадр в RGBA PNG с сохранением прозрачности без мыла и артефактов.
- 🔄 **Мультиформатная поддержка**: умеет работать с векторными `.tgs`, несжатыми Lottie `.json`, статическими `.webp`, а также видео-эмодзи `.webm` (через `ffmpeg`).
- 📏 **Динамическая типографика**: автоматически масштабирует размер шрифта `BebasNeue-Regular.ttf` под длину названия пака, идеально центрируя заголовок.
- 📐 **Адаптивная сетка эмодзи**: вычисляет оптимальное число рядов (2 или 3 ряда) для 12–18 эмодзи, центрируя элементы каждого ряда и соблюдая правильные отступы.
- 💎 **Качество без сжатия**: результат отправляется пользователю как несжатый документ 1920×1200 с интерактивной Inline-кнопкой для моментальной установки набора в Telegram.
- 🛡 **Non-blocking архитектура**: тяжелый рендеринг вынесен в пул потоков (`asyncio.to_thread`), бот моментально отвечает на команды и не зависает под нагрузкой.

---

## 🛠 Системные зависимости Linux

Для работы с векторной графикой Lottie и шрифтами требуются графические библиотеки Cairo / Pango.

### Ubuntu / Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    python3-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libffi-dev \
    ffmpeg
```

### Fedora / RHEL / CentOS:
```bash
sudo dnf install -y \
    gcc-c++ \
    cmake \
    python3-devel \
    cairo-devel \
    pango-devel \
    libffi-devel \
    ffmpeg
```

### Arch Linux:
```bash
sudo pacman -S base-devel cmake python cairo pango libffi ffmpeg
```

---

## 🚀 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/photoshopgame/telegram-emoji-banner-bot.git
cd telegram-emoji-banner-bot
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка Python-зависимостей
```bash
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

> **Совет:** Рекомендуемый и самый стабильный движок — `lottie cairosvg` (уже указан в `requirements.txt`). Также поддерживается официальная C++ библиотека Samsung `rlottie-python`.

### 4. Настройка переменных окружения
Скопируйте шаблон конфигурации:
```bash
cp .env.example .env
```
Откройте файл `.env` и вставьте ваш токен бота от [@BotFather](https://t.me/BotFather):
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 5. Запуск бота
```bash
python main.py
```

---

## 📁 Структура проекта

```text
├── background.png            # Шаблон фона (1920x1200)
├── BebasNeue-Regular.ttf     # Акцентный шрифт для заголовка
├── main.py                   # Основная логика бота на aiogram 3.x
├── render.py                 # Модуль парсинга TGS, рендера и сборки баннера
├── requirements.txt          # Python-зависимости
├── .env.example              # Пример файла с переменными окружения
├── .gitignore                # Исключение секретов, кэша и виртуальных сред
├── LICENSE                   # Лицензия MIT
└── README.md                 # Документация проекта
```

---

## 🐣 Пасхалка

В боте спрятана секретная пасхалка от автора:
- Отправьте боту команду `/lux` или просто напишите `lux` / `photoshopgame` в чат!

---

## 👨‍💻 Автор

**Lux**
- Telegram: [@photoshopgame](https://t.me/photoshopgame)
- GitHub: [@photoshopgame](https://github.com/photoshopgame)

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE). Вы можете свободно использовать, модифицировать и распространять данный код.
