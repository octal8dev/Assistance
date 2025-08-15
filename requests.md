# Руководство по тестированию API в Postman

## Настройка окружения

### 1. Создание коллекции
1. Откройте Postman
2. Создайте новую коллекцию: `Django Blog API`
3. В настройках коллекции добавьте переменные:
   - `base_url`: `http://127.0.0.1:8000`
   - `access_token`: (будет заполнено автоматически)
   - `refresh_token`: (будет заполнено автоматически)
   - `category_id`: (будет заполнено автоматически)
   - `category_slug`: (будет заполнено автоматически)
   - `post_id`: (будет заполнено автоматически)
   - `post_slug`: (будет заполнено автоматически)

### 2. Настройка авторизации для коллекции
1. Перейдите в настройки коллекции → Authorization
2. Выберите Type: `Bearer Token`
3. В поле Token введите: `{{access_token}}`

## Тестирование аутентификации

### 1. Регистрация пользователя
**POST** `{{base_url}}/api/v1/auth/register/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User"
}
```

**Tests (вкладка Tests):**
```javascript
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Response contains tokens", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('access');
    pm.expect(jsonData).to.have.property('refresh');
    pm.expect(jsonData).to.have.property('user');
    
    // Сохраняем токены в переменные окружения
    pm.environment.set("access_token", jsonData.access);
    pm.environment.set("refresh_token", jsonData.refresh);
});

pm.test("User data is correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.user.email).to.eql("test@example.com");
    pm.expect(jsonData.user.username).to.eql("testuser");
});
```

### 2. Вход пользователя
**POST** `{{base_url}}/api/v1/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "email": "test@example.com",
    "password": "TestPassword123!"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Login successful", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.message).to.eql("User login successfully");
    
    // Обновляем токены
    pm.environment.set("access_token", jsonData.access);
    pm.environment.set("refresh_token", jsonData.refresh);
});
```

### 3. Получение профиля пользователя
**GET** `{{base_url}}/api/v1/auth/profile/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Profile data is returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('email');
    pm.expect(jsonData).to.have.property('posts_count');
    pm.expect(jsonData).to.have.property('comments_count');
});
```

### 4. Обновление профиля
**PATCH** `{{base_url}}/api/v1/auth/profile/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "bio": "This is my updated bio"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Profile updated successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.first_name).to.eql("Updated");
    pm.expect(jsonData.last_name).to.eql("Name");
    pm.expect(jsonData.bio).to.eql("This is my updated bio");
});
```

### 5. Смена пароля
**PUT** `{{base_url}}/api/v1/auth/change-password/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "old_password": "TestPassword123!",
    "new_password": "NewTestPassword123!",
    "new_password_confirm": "NewTestPassword123!"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Password changed successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.message).to.eql("Password changed successfully");
});
```

### 6. Обновление токена
**POST** `{{base_url}}/api/v1/auth/token/refresh/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "refresh": "{{refresh_token}}"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("New access token received", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('access');
    pm.environment.set("access_token", jsonData.access);
});
```

### 7. Выход из системы
**POST** `{{base_url}}/api/v1/auth/logout/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "refresh_token": "{{refresh_token}}"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Logout successful", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.message).to.eql("Logout successful");
    
    // Очищаем токены
    pm.environment.unset("access_token");
    pm.environment.unset("refresh_token");
});
```

## Тестирование категорий

### 1. Получение списка категорий
**GET** `{{base_url}}/api/v1/posts/categories/`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Categories list is returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Category structure is correct", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 0) {
        var category = jsonData.results[0];
        pm.expect(category).to.have.property('id');
        pm.expect(category).to.have.property('name');
        pm.expect(category).to.have.property('slug');
        pm.expect(category).to.have.property('posts_count');
    }
});
```

### 2. Создание новой категории
**POST** `{{base_url}}/api/v1/posts/categories/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "name": "Technology",
    "description": "All about latest technology trends"
}
```

**Tests:**
```javascript
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Category created successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.name).to.eql("Technology");
    pm.expect(jsonData.description).to.eql("All about latest technology trends");
    pm.expect(jsonData).to.have.property('slug');
    
    // Сохраняем ID и slug для последующих тестов
    pm.environment.set("category_id", jsonData.id);
    pm.environment.set("category_slug", jsonData.slug);
});

pm.test("Slug is auto-generated", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.slug).to.eql("technology");
});
```

### 3. Получение конкретной категории
**GET** `{{base_url}}/api/v1/posts/categories/{{category_slug}}/`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Category details are correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.name).to.eql("Technology");
    pm.expect(jsonData.slug).to.eql(pm.environment.get("category_slug"));
});
```

### 4. Обновление категории
**PATCH** `{{base_url}}/api/v1/posts/categories/{{category_slug}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "description": "Updated description for technology category"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Category updated successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.description).to.eql("Updated description for technology category");
});
```

### 5. Поиск категорий
**GET** `{{base_url}}/api/v1/posts/categories/?search=tech`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Search results contain relevant categories", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        var foundTech = jsonData.results.some(category => 
            category.name.toLowerCase().includes('tech')
        );
        pm.expect(foundTech).to.be.true;
    }
});
```

## Тестирование постов

### 1. Получение списка постов
**GET** `{{base_url}}/api/v1/posts/`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Posts list is returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Post structure is correct", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 0) {
        var post = jsonData.results[0];
        pm.expect(post).to.have.property('id');
        pm.expect(post).to.have.property('title');
        pm.expect(post).to.have.property('slug');
        pm.expect(post).to.have.property('author');
        pm.expect(post).to.have.property('category');
        pm.expect(post).to.have.property('views_count');
        pm.expect(post).to.have.property('comments_count');
    }
});
```

### 2. Создание нового поста
**POST** `{{base_url}}/api/v1/posts/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "title": "My First Blog Post",
    "content": "This is the content of my first blog post. It contains detailed information about various topics and provides valuable insights for readers.",
    "category": {{category_id}},
    "status": "published"
}
```

**Tests:**
```javascript
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Post created successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.title).to.eql("My First Blog Post");
    pm.expect(jsonData.status).to.eql("published");
    pm.expect(jsonData).to.have.property('slug');
    pm.expect(jsonData).to.have.property('author');
    
    // Сохраняем ID и slug для последующих тестов
    pm.environment.set("post_id", jsonData.id);
    pm.environment.set("post_slug", jsonData.slug);
});

pm.test("Slug is auto-generated", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.slug).to.eql("my-first-blog-post");
});
```

### 3. Создание поста с изображением
**POST** `{{base_url}}/api/v1/posts/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Body (form-data):**
- Key: `title`, Type: Text, Value: "Post with Image"
- Key: `content`, Type: Text, Value: "This post contains an image"
- Key: `category`, Type: Text, Value: `{{category_id}}`
- Key: `status`, Type: Text, Value: "published"
- Key: `image`, Type: File, Value: выберите изображение

**Tests:**
```javascript
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Post with image created successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.title).to.eql("Post with Image");
    pm.expect(jsonData).to.have.property('image');
    pm.expect(jsonData.image).to.not.be.null;
});
```

### 4. Получение конкретного поста
**GET** `{{base_url}}/api/v1/posts/{{post_slug}}/`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Post details are correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.title).to.eql("My First Blog Post");
    pm.expect(jsonData.slug).to.eql(pm.environment.get("post_slug"));
    pm.expect(jsonData).to.have.property('author_info');
    pm.expect(jsonData).to.have.property('category_info');
});

pm.test("Author info is present", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.author_info).to.have.property('username');
    pm.expect(jsonData.author_info).to.have.property('full_name');
});

pm.test("Views count incremented", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.views_count).to.be.at.least(1);
});
```

### 5. Обновление поста
**PATCH** `{{base_url}}/api/v1/posts/{{post_slug}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "title": "My Updated Blog Post",
    "content": "This is the updated content of my blog post with more detailed information."
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Post updated successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.title).to.eql("My Updated Blog Post");
    pm.expect(jsonData.content).to.eql("This is the updated content of my blog post with more detailed information.");
});
```

### 6. Получение своих постов
**GET** `{{base_url}}/api/v1/posts/my-posts/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("My posts are returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("All posts belong to current user", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 0) {
        jsonData.results.forEach(function(post) {
            pm.expect(post.author).to.eql("testuser"); // или email пользователя
        });
    }
});
```

### 7. Фильтрация постов по категории
**GET** `{{base_url}}/api/v1/posts/?category={{category_id}}`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Posts filtered by category", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        jsonData.results.forEach(function(post) {
            pm.expect(post.category).to.eql("Technology");
        });
    }
});
```

### 8. Поиск постов
**GET** `{{base_url}}/api/v1/posts/?search=blog`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Search results are relevant", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        var foundRelevant = jsonData.results.some(post => 
            post.title.toLowerCase().includes('blog') || 
            post.content.toLowerCase().includes('blog')
        );
        pm.expect(foundRelevant).to.be.true;
    }
});
```

### 9. Сортировка постов
**GET** `{{base_url}}/api/v1/posts/?ordering=-views_count`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Posts sorted by views count descending", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 1) {
        for (let i = 0; i < jsonData.results.length - 1; i++) {
            pm.expect(jsonData.results[i].views_count).to.be.at.least(jsonData.results[i + 1].views_count);
        }
    }
});
```

### 10. Получение популярных постов
**GET** `{{base_url}}/api/v1/posts/popular/`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Popular posts are returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.be.an('array');
    pm.expect(jsonData.length).to.be.at.most(10);
});

pm.test("Posts are sorted by views", function () {
    var jsonData = pm.response.json();
    if (jsonData.length > 1) {
        for (let i = 0; i < jsonData.length - 1; i++) {
            pm.expect(jsonData[i].views_count).to.be.at.least(jsonData[i + 1].views_count);
        }
    }
});
```

### 11. Получение последних постов
**GET** `{{base_url}}/api/v1/posts/recent/`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Recent posts are returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.be.an('array');
    pm.expect(jsonData.length).to.be.at.most(10);
});

pm.test("Posts are sorted by creation date", function () {
    var jsonData = pm.response.json();
    if (jsonData.length > 1) {
        for (let i = 0; i < jsonData.length - 1; i++) {
            var date1 = new Date(jsonData[i].created_at);
            var date2 = new Date(jsonData[i + 1].created_at);
            pm.expect(date1.getTime()).to.be.at.least(date2.getTime());
        }
    }
});
```

### 12. Получение постов по категории
**GET** `{{base_url}}/api/v1/posts/categories/{{category_slug}}/posts/`

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Category and posts data returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('category');
    pm.expect(jsonData).to.have.property('posts');
    pm.expect(jsonData.posts).to.be.an('array');
});

pm.test("Category info is correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.category.slug).to.eql(pm.environment.get("category_slug"));
});
```

## Тестирование ошибок

### 1. Создание поста без авторизации
**POST** `{{base_url}}/api/v1/posts/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "title": "Unauthorized Post",
    "content": "This should fail"
}
```

**Expected:** Status 401, ошибка аутентификации

### 2. Редактирование чужого поста
Для этого теста нужно создать второго пользователя и попытаться отредактировать пост первого пользователя.

**PATCH** `{{base_url}}/api/v1/posts/{{post_slug}}/`

**Headers:**
```
Authorization: Bearer {{other_user_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "title": "Trying to edit someone else's post"
}
```

**Expected:** Status 403, ошибка доступа

### 3. Создание поста с невалидными данными
**POST** `{{base_url}}/api/v1/posts/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "title": "",
    "content": "Content without title"
}
```

**Expected:** Status 400, ошибка валидации

### 4. Получение несуществующего поста
**GET** `{{base_url}}/api/v1/posts/non-existent-post/`

**Expected:** Status 404, пост не найден

### 5. Создание категории с существующим именем
**POST** `{{base_url}}/api/v1/posts/categories/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "name": "Technology"
}
```

**Expected:** Status 400, ошибка уникальности

## Последовательность тестирования

1. **Регистрация пользователя** → Получение токенов
2. **Создание категории** → Сохранение category_id и category_slug
3. **Создание поста** → Сохранение post_id и post_slug
4. **Тестирование CRUD операций с постами**
5. **Тестирование фильтрации и поиска**
6. **Тестирование специальных эндпоинтов** (популярные, последние)
7. **Тестирование ошибок и edge cases**
8. **Удаление тестовых данных**

## Удаление тестовых данных

### Удаление поста
**DELETE** `{{base_url}}/api/v1/posts/{{post_slug}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Tests:**
```javascript
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});
```

### Удаление категории
**DELETE** `{{base_url}}/api/v1/posts/categories/{{category_slug}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Tests:**
```javascript
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});
```

## Создание тестового набора

### Pre-request Script для коллекции:
```javascript
// Проверяем, запущен ли Django сервер
pm.sendRequest({
    url: pm.environment.get("base_url"),
    method: 'GET'
}, function (err, response) {
    if (err) {
        console.log("Django server is not running on " + pm.environment.get("base_url"));
    }
});
```

### Collection Tests:
```javascript
pm.test("Django server is accessible", function () {
    pm.response.to.not.be.error;
});
```

## Запуск Django сервера

Перед тестированием убедитесь, что Django сервер запущен:

```bash
# В терминале
python manage.py runserver
```

## Дополнительные тесты

### Тест пагинации
**GET** `{{base_url}}/api/v1/posts/?page=1&page_size=5`

**Tests:**
```javascript
pm.test("Pagination works correctly", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('count');
    pm.expect(jsonData).to.have.property('next');
    pm.expect(jsonData).to.have.property('previous');
    pm.expect(jsonData.results.length).to.be.at.most(5);
});
```

### Тест загрузки изображения поста
**PATCH** `{{base_url}}/api/v1/posts/{{post_slug}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Body (form-data):**
- Key: `image`, Type: File, Value: выберите изображение

### Тест комбинированной фильтрации
**GET** `{{base_url}}/api/v1/posts/?category={{category_id}}&search=blog&ordering=-created_at`

## Автоматизация тестов

Для автоматического запуска всех тестов используйте Collection Runner:
1. Нажмите на коллекцию → Run collection
2. Выберите все запросы в правильном порядке
3. Установите задержку между запросами (500ms)
4. Запустите тесты

## Рекомендуемый порядок выполнения тестов:

1. Аутентификация (регистрация, вход)
2. Создание категории
3. Создание постов
4. Получение и фильтрация постов
5. Обновление постов
6. Специальные эндпоинты
7. Тестирование ошибок
8. Удаление тестовых данных
9. Выход из системы

Это руководство поможет вам протестировать все функции вашего блог API и убедиться в их корректной работе.