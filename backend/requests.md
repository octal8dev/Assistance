# Руководство по API для Frontend-разработчика

## 1. Введение
Это руководство предоставляет исчерпывающую информацию обо всех API-эндпоинтах, доступных в бэкенде. Оно предназначено для frontend-разработчиков, чтобы обеспечить правильную интеграцию с API. Так же оно создано, чтобы проводить тесты на POSTMAN.

### 1.1. Базовый URL
Все эндпоинты, описанные в этом документе, используют следующий базовый URL:
`http://127.0.0.1:8000/api/v1/`

### 1.2. Авторизация
Большинство эндпоинтов требуют аутентификации. Для этого необходимо передавать Access Token в заголовке `Authorization`.
- **Header:** `Authorization`
- **Value:** `Bearer <your_access_token>`

Access Token получается при регистрации или входе в систему.

### 1.3. Переменные для Postman
Для удобства тестирования рекомендуется создать в Postman следующие переменные:
- `base_url`: `http://127.0.0.1:8000`
- `access_token`: (будет получен после логина)
- `refresh_token`: (будет получен после логина)
- `user_id`: (ID пользователя)
- `subscription_plan_id`: (ID тарифного плана)
- `payment_id`: (ID платежа)
- `assistante_bot_settings_id`: (ID настроек бота)
- `managed_chat_id`: (ID управляемого чата)


## 2. Аутентификация и Управление профилем (`/auth/`)

### 2.1. Регистрация нового пользователя
- **Эндпоинт:** `POST /api/v1/auth/register/`
- **Описание:** Создает нового пользователя в системе.
- **Авторизация:** Не требуется.

**Тело запроса (JSON):**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "StrongPassword123!",
    "password_confirm": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User"
}
```

**Ответ (201 Created):**
```json
{
    "user": {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    },
    "access": "<access_token>",
    "refresh": "<refresh_token>"
}
```

### 2.2. Вход в систему
- **Эндпоинт:** `POST /api/v1/auth/login/`
- **Описание:** Аутентифицирует пользователя и возвращает токены.
- **Авторизация:** Не требуется.

**Тело запроса (JSON):**
```json
{
    "email": "test@example.com",
    "password": "StrongPassword123!"
}
```

**Ответ (200 OK):**
```json
{
    "message": "User login successfully",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com"
    },
    "access": "<new_access_token>",
    "refresh": "<new_refresh_token>"
}
```

### 2.3. Аутентификация через Google
- **Эндпоинт:** `POST /api/v1/auth/google/`
- **Описание:** Аутентифицирует пользователя с помощью Google. Если пользователь не существует, он будет создан. Возвращает токены.
- **Авторизация:** Не требуется.

**Тело запроса (JSON):**
```json
{
    "access_token": "<google_access_token>"
}
```

**Ответ (200 OK):**
```json
{
    "user": {
        "id": 1,
        "username": "googleuser",
        "email": "user@gmail.com",
        "first_name": "Google",
        "last_name": "User"
    },
    "access": "<access_token>",
    "refresh": "<refresh_token>",
    "message": "Пользователь успешно вошел через Google"
}
```

### 2.4. Просмотр и редактирование профиля
- **Эндпоинт:** `GET /api/v1/auth/profile/` (просмотр), `PATCH /api/v1/auth/profile/` (редактирование)
- **Описание:** Позволяет получить или обновить информацию о текущем пользователе.
- **Авторизация:** Требуется.

**Ответ `GET` (200 OK):**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "full_name": "Test User",
    "avatar": null,
    "bio": "My bio...",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T10:00:00Z",
    "posts_count": 5,
    "comments_count": 12
}
```

**Тело запроса `PATCH` (JSON):**
```json
{
    "first_name": "Updated First Name",
    "bio": "My new bio."
}
```

**Ответ `PATCH` (200 OK):** Обновленные данные пользователя.

### 2.5. Смена пароля
- **Эндпоинт:** `POST /api/v1/auth/change-password/`
- **Описание:** Позволяет пользователю изменить свой пароль.
- **Авторизация:** Требуется.

**Тело запроса (JSON):**
```json
{
    "old_password": "StrongPassword123!",
    "new_password": "EvenStrongerPassword456!",
    "new_password_confirm": "EvenStrongerPassword456!"
}
```

**Ответ (200 OK):**
```json
{
    "message": "Password changed successfully"
}
```

### 2.6. Обновление токена
- **Эндпоинт:** `POST /api/v1/auth/token/refresh/`
- **Описание:** Получает новый `access_token` с помощью `refresh_token`.
- **Авторизация:** Не требуется.

**Тело запроса (JSON):**
```json
{
    "refresh": "<your_refresh_token>"
}
```

**Ответ (200 OK):**
```json
{
    "access": "<new_access_token>"
}
```

## 3. Подписки (`/subscribe/`)

### 3.1. Список тарифных планов
- **Эндпоинт:** `GET /api/v1/subscribe/plans/`
- **Описание:** Возвращает список всех доступных тарифных планов.
- **Авторизация:** Не требуется.

**Ответ (200 OK):**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Premium",
            "price": "29.99",
            "duration_days": 30,
            "features": {
                "max_chats": 10,
                "analytics_access": true
            },
            "is_active": true,
            "created_at": "2023-10-27T10:00:00Z"
        }
    ]
}
```

### 3.2. Детальная информация о тарифном плане
- **Эндпоинт:** `GET /api/v1/subscribe/plans/{id}/`
- **Авторизация:** Не требуется.

### 3.3. Статус подписки пользователя
- **Эндпоинт:** `GET /api/v1/subscribe/status/`
- **Описание:** Возвращает информацию о текущей подписке пользователя.
- **Авторизация:** Требуется.

**Ответ (200 OK):**
```json
{
    "has_subscription": true,
    "is_active": true,
    "subscription": {
        "id": 1,
        "status": "active",
        // ... другие поля из SubscriptionSerializer
    }
}
```

### 3.4. История подписки
- **Эндпоинт:** `GET /api/v1/subscribe/history/`
- **Описание:** Возвращает историю действий с подпиской пользователя.
- **Авторизация:** Требуется.

## 4. Платежи (`/payment/`)

### 4.1. Создание сессии для оплаты (Stripe)
- **Эндпоинт:** `POST /api/v1/payment/create-checkout-session/`
- **Описание:** Создает платежную сессию в Stripe для покупки подписки.
- **Авторизация:** Требуруется.

**Тело запроса (JSON):**
```json
{
    "subscription_plan_id": 1,
    "payment_method": "stripe",
    "success_url": "http://your-frontend.com/payment/success?session_id={CHECKOUT_SESSION_ID}",
    "cancel_url": "http://your-frontend.com/payment/cancel"
}
```

**Ответ (201 Created):**
```json
{
    "checkout_url": "https://checkout.stripe.com/...",
    "session_id": "cs_test_...",
    "payment_id": 1
}
```

### 4.2. Статус платежа
- **Эндпоинт:** `GET /api/v1/payment/payments/{payment_id}/status/`
- **Авторизация:** Требуется.

### 4.3. Список платежей пользователя
- **Эндпоинт:** `GET /api/v1/payment/payments/`
- **Авторизация:** Требуется.

## 5. Управление Telegram-Ассистентом (`/assistante/`)

### 5.1. Получение и обновление настроек бота
- **Эндпоинт:** `GET /api/v1/assistante/settings/`, `PATCH /api/v1/assistante/settings/`
- **Описание:** Управляет настройками Telegram-бота для текущего пользователя. `GET` возвращает единственную запись настроек, `PATCH` обновляет её.
- **Авторизация:** Требуется.

**Ответ `GET` (200 OK):**
```json
{
    "id": 1,
    "is_active": true,
    "prompt": {
        "system_prompt": "You are a helpful assistant.",
        "user_prompt": "Analyze the sentiment of the following message: {message}"
    },
    "managed_chats": [
        {
            "id": 1,
            "chat_id": "-100123456789",
            "title": "My Awesome Group",
            "is_active": true
        }
    ],
    "activity_stats": [
        {
            "date": "2023-10-27",
            "messages_processed": 150,
            "most_frequent_topic": "customer support"
        }
    ]
}
```

**Тело запроса `PATCH` (JSON):**
*Вы можете обновлять только необходимые поля.*
```json
{
    "is_active": false,
    "prompt": {
        "system_prompt": "You are an expert in marketing analysis."
    }
}
```

### 5.2. Создание настроек бота (если не существуют)
- **Эндпоинт:** `POST /api/v1/assistante/settings/`
- **Описание:** Создает объект настроек для пользователя. Обычно выполняется один раз.
- **Авторизация:** Требуется.

**Тело запроса (JSON):**
```json
{
    "api_id": "1234567",
    "api_hash": "your_api_hash_string",
    "prompt": {
        "system_prompt": "Initial system prompt.",
        "user_prompt": "Initial user prompt."
    }
}
```
**Важно:** `api_id` и `api_hash` являются `write_only` и не будут отображаться при GET-запросах.

### 5.3. Список отслеживаемых чатов
- **Эндпоинт:** `GET /api/v1/assistante/managed-chats/`
- **Описание:** Возвращает список чатов, которыми управляет бот.
- **Авторизация:** Требуется.

### 5.4. Обновление отслеживаемого чата
- **Эндпоинт:** `PATCH /api/v1/assistante/managed-chats/{id}/`
- **Описание:** Позволяет активировать или деактивировать отслеживание конкретного чата.
- **Авторизация:** Требуется.

**Тело запроса `PATCH` (JSON):**
```json
{
    "is_active": false
}
```

**Ответ (200 OK):** Обновленные данные чата.

