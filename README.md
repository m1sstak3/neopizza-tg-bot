<div align="center">
  <h1>🍕 NeoPizza Dark Kitchen – Telegram Bot</h1>
  <p><b>Профессиональная экосистема для доставки еды: управление заказами, умный роутинг курьеров и DDD-архитектура.</b></p>

  <div>
    <img src="https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Aiogram_3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Aiogram" />
    <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
    <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery" />
    <img src="https://img.shields.io/badge/DDD_Architecture-8A2BE2?style=for-the-badge&logo=codeigniter&logoColor=white" alt="DDD" />
  </div>
</div>

---

## 📱 Демонстрация интерфейсов (Роли)

<table align="center">
  <tr>
    <td align="center">
      <b>🍔 Клиент (Оформление заказа)</b><br>
      <img src="https://github.com/user-attachments/assets/e7187138-a78a-4e8b-89b9-e7261bd50e52" width="400" />
    </td>
    <td align="center">
      <b>💳 Кассир (Прием заказа)</b><br>
      <img src="https://github.com/user-attachments/assets/a9a516bc-b440-4014-9f7d-c410a6b52e1e" width="400" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <b>👨‍🍳 Шеф-повар (Кухня)</b><br>
      <img src="https://github.com/user-attachments/assets/4fb631b7-3e52-4cc2-891f-8902a2bfa52a" width="400" />
    </td>
    <td align="center">
      <b>🛵 Курьер (Доставка)</b><br>
      <img src="https://github.com/user-attachments/assets/c37d43a6-82ca-4776-90d8-4be4e810904e" width="400" />
    </td>
  </tr>
  <tr>
    <td align="center">
      <b>📊 Админ (Отчеты)</b><br>
      <img src="https://github.com/user-attachments/assets/04b73d9f-e81a-4de9-b4cb-c39847ecc77f" width="400" />
    </td>
    <td align="center">
      <b>👑 SuperAdmin (Управление)</b><br>
      <img src="https://github.com/user-attachments/assets/e7fd8f31-9fcd-4ef3-a799-27592e3bbb84" width="400" />
    </td>
  </tr>
</table>

---

## ✨ Ключевые возможности

Комплексное алгоритмическое и инфраструктурное решение для службы доставки полного цикла. Бот выступает единой точкой контакта для четырех ключевых ролей.

* 🔐 **Умный ролевой доступ (RBAC):** Middleware мгновенно маршрутизирует пользователей в зависимости от их роли (`Client`, `Cashier`, `Chef`, `Courier`, `Admin`).
* 🛒 **Асинхронная корзина покупок:** Сверхбыстрое временное хранилище корзины реализовано исключительно в RAM (кластеры Redis).
* ⚙️ **Фоновые процессы (Celery):**
  * Динамический расчет ETA (времени доставки) на основе текущей загруженности кухни.
  * Автоматическое распределение заказов между курьерами с привязкой к зонам.
  * Активация предзаказов по расписанию (CRON).
* 💸 **Нативная оплата:** Полная поддержка Telegram Payments UI для быстрых и безопасных безналичных платежей.

---

## 🏗 Архитектура (Clean / DDD)

Проект строго придерживается многослойной архитектуры Domain-Driven Design, разделяя бизнес-логику и инфраструктуру. Реализован строгий DI Pipeline (внедрение зависимостей).

<details>
<summary><b>📂 Посмотреть структуру слоев</b></summary>
<br>

```text
├── domain/           # Базовые сущности, value-objects и бизнес-правила
├── infrastructure/   # Репозитории (БД), сессии Redis, внешние API
├── application/      # Use-cases и фоновые процессы (Celery)
└── presentation/     # Aiogram хэндлеры, FSM контексты и Middleware
```
</details>

---

## 🚀 Быстрый старт

Проект управляется через `Poetry` и готов к запуску в контейнерах.

### 1. Подготовка окружения
```bash
git clone https://github.com/m1sstak3/neopizza-dark-kitchen.git
cd neopizza-dark-kitchen
cp .env.example .env
```
*Укажите в `.env` ваш `BOT_TOKEN`, данные для PostgreSQL и Redis.*

### 2. Запуск инфраструктуры
Поднимите локальные контейнеры PostgreSQL и Redis:
```bash
docker-compose up -d
```

### 3. Установка и запуск бота
```bash
# Инициализация окружения
poetry install

# Применение миграций БД
poetry run alembic upgrade head

# Запуск основного приложения
poetry run python -m src.presentation.bot
```

---

## 📈 Масштабируемость и Highload

* **Stateless Хэндлеры:** Экземпляры бота не хранят состояние внутри себя. Вся информация (FSM, корзины) находится в Redis, что позволяет масштабироваться горизонтально.
* **Пул соединений:** Встроенный асинхронный пул соединений SQLAlchemy (`asyncpg`) исключает утечки соединений.
* **Распределенные очереди:** Тяжелые операции вынесены в Celery-воркеры, которые масштабируются независимо от API бота.
* **Production-Ready:** Строгая статическая типизация (`mypy`) и защита через Privacy Gateways.

---

<div align="center">
  <b>Developed with ❤️ by m1sstak3</b>
</div>
