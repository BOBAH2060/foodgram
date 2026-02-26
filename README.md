# README.md для проекта Foodgram

## Название проекта
**Foodgram**

## Описание
Foodgram — веб‑приложение для публикации и просмотра кулинарных рецептов. Проект демонстрирует работу с:
- контейнеризацией (Docker);
- CI/CD‑пайплайном через GitHub Actions.

## Автор проекта
BOBAH2060 (Владимир Маслов)

## Ссылки
- **Репозиторий**: https://github.com/BOBAH2060/foodgram
- **Развёрнутый проект**: https://foodgramstudents.hopto.org

## Используемые технологии
- **Backend**: Python, Django
- **Frontend**: HTML/CSS, JavaScript
- **Контейнеризация**: Docker
- **CI/CD**: GitHub Actions
- **Оркестрация**: Docker Compose
- **База данных**: PostgreSQL
- **Веб‑сервер**: Nginx

## Версии проекта: продакшн vs разработка

### Разработка (development)
- Отладка включена (`DEBUG = True` в Django).
- Локальные настройки (например, SQLite).
- Логи выводятся в консоль.
- Порт по умолчанию: `8000`.
- HTTPS не используется.

### Продакшн (production)
- Отладка отключена (`DEBUG = False`).
- Используется PostgreSQL.
- Статические файлы обслуживаются через Nginx/CDN.
- Порты: `80`/`443` (с HTTPS).
- Включены кеширование и оптимизация производительности.
- Логи записываются в файлы/системы мониторинга.

### Когда использовать
- **Разработка**: для локальной отладки и тестирования новых функций.
- **Продакшн**: для развёртывания на сервере и работы с реальными пользователями.

## Настройка окружения (.env‑файл)

Создайте файл `.env` в корне проекта. Ниже — **шаблон с примерами значений**. Замените их на свои реальные данные!

## Секретный ключ Django (сгенерируйте свой!)
- SECRET_KEY='django-insecure-ваш-уникальный-ключ-здесь'


## Режим отладки: True — разработка, False — продакшн
- DEBUG=False


## Разрешённые хосты (домены и IP, через запятую без пробелов)
- ALLOWED_HOSTS=ваш-домен.ru,192.168.1.100

### Для разработки можно использовать:
- ALLOWED_HOSTS=localhost,127.0.0.1,[::1]

### Настройки PostgreSQL ###
- POSTGRES_DB=имя_вашей_базы
- POSTGRES_USER=ваш_пользователь_бд
- POSTGRES_PASSWORD=ваш_пароль_бд

## Настройки Django для подключения к БД ##
- DB_NAME=имя_вашей_базы
- DB_USER=ваш_пользователь_бд
- DB_PASSWORD=ваш_пароль_бд
- DB_HOST=db
- DB_PORT=5432


## Инструкция по развёртыванию ##
Локальное развёртывание
Клонируйте репозиторий:


```bash
git clone https://github.com/BOBAH2060/foodgram.git
cd foodgram
```
Подготовьте окружение:

Установите Docker и Docker Compose.
Создайте файл .env в корневой папке (используйте шаблон выше).
Запустите контейнеры:

```bash
docker compose up -d
```

Создайте суперпользователя (опционально):

```bash
docker compose exec backend python manage.py createsuperuser
```
Проект будет доступен по адресу: http://localhost:8000

Удаленное развёртывание (на сервере)
Подготовьте сервер:

ОС: Ubuntu 20.04/22.04.
Установите Docker, Docker Compose, git.
Клонируйте проект и настройте среду:

```bash
ssh user@your_server_ip
git clone https://github.com/BOBAH2060/foodgram.git
cd kittygram_final
```

Настройте файл .env для продакшн‑режима (используйте реальные секретные значения!).

Запустите контейнеры в режиме продакшн:

```bash
docker compose -f docker-compose.production.yml up -d
```

Настройте сеть:

Настройте Nginx или Caddy для проксирования запросов.

Настройте HTTPS (рекомендуется использовать Certbot для получения сертификатов Let's Encrypt).

Статус проекта (Бейдж GitHub Actions)
![GitHub Actions](https://github.com/BOBAH2060/kittygram_final/actions/workflows/main.yml/badge.svg)
