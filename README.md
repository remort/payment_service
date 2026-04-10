# Payment Service

Асинхронный сервис процессинга платежей.

## Быстрый запуск

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd payment_service
```

2. Создайте файл .env из примера:

```bash
cp .env.example .env
```

3. Запустите сервисы:

```bash
make up
```

4. Примените миграции (автоматически при запуске, но можно вручную):

```bash
make migrate
```

5. Проверьте работу:

```bash
bash test_api.sh
```
