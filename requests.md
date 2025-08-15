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
   - `comment_id`: (будет заполнено автоматически)
   - `parent_comment_id`: (будет заполнено автоматически)

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

## Тестирование комментариев

### 1. Получение списка всех комментариев
**GET** `{{base_url}}/api/v1/comments/`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comments list is returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Comment structure is correct", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 0) {
        var comment = jsonData.results[0];
        pm.expect(comment).to.have.property('id');
        pm.expect(comment).to.have.property('content');
        pm.expect(comment).to.have.property('author');
        pm.expect(comment).to.have.property('author_info');
        pm.expect(comment).to.have.property('parent');
        pm.expect(comment).to.have.property('is_active');
        pm.expect(comment).to.have.property('replies_count');
        pm.expect(comment).to.have.property('is_reply');
        pm.expect(comment).to.have.property('created_at');
    }
});
```

### 2. Создание основного комментария
**POST** `{{base_url}}/api/v1/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "post": {{post_id}},
    "content": "This is my first comment on this amazing blog post! Thank you for sharing such valuable information."
}
```

**Tests:**
```javascript
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Comment created successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.content).to.eql("This is my first comment on this amazing blog post! Thank you for sharing such valuable information.");
    pm.expect(jsonData.post).to.eql(pm.environment.get("post_id"));
    pm.expect(jsonData.parent).to.be.null;
    pm.expect(jsonData.is_reply).to.be.false;
    pm.expect(jsonData.is_active).to.be.true;
    
    // Сохраняем ID комментария для дальнейших тестов
    pm.environment.set("comment_id", jsonData.id);
});

pm.test("Author info is included", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.author_info).to.have.property('username');
    pm.expect(jsonData.author_info).to.have.property('full_name');
    pm.expect(jsonData.author_info.username).to.eql("testuser");
});
```

### 3. Создание ответа на комментарий
**POST** `{{base_url}}/api/v1/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "post": {{post_id}},
    "parent": {{comment_id}},
    "content": "Thank you for your comment! I'm glad you found the post helpful. Feel free to ask any questions."
}
```

**Tests:**
```javascript
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Reply comment created successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.content).to.eql("Thank you for your comment! I'm glad you found the post helpful. Feel free to ask any questions.");
    pm.expect(jsonData.post).to.eql(pm.environment.get("post_id"));
    pm.expect(jsonData.parent).to.eql(pm.environment.get("comment_id"));
    pm.expect(jsonData.is_reply).to.be.true;
    pm.expect(jsonData.is_active).to.be.true;
    
    // Сохраняем ID ответа для дальнейших тестов
    pm.environment.set("reply_comment_id", jsonData.id);
});
```

### 4. Получение комментариев к конкретному посту
**GET** `{{base_url}}/api/v1/comments/post/{{post_id}}/`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Post comments data structure is correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('post');
    pm.expect(jsonData).to.have.property('comments');
    pm.expect(jsonData).to.have.property('comments_count');
    pm.expect(jsonData.comments).to.be.an('array');
});

pm.test("Post info is included", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.post).to.have.property('id');
    pm.expect(jsonData.post).to.have.property('title');
    pm.expect(jsonData.post).to.have.property('slug');
    pm.expect(jsonData.post.id).to.eql(pm.environment.get("post_id"));
});

pm.test("Comments include replies", function () {
    var jsonData = pm.response.json();
    if (jsonData.comments.length > 0) {
        var mainComment = jsonData.comments.find(comment => comment.parent === null);
        if (mainComment) {
            pm.expect(mainComment).to.have.property('replies');
            pm.expect(mainComment.replies).to.be.an('array');
            pm.expect(mainComment.replies_count).to.be.at.least(0);
        }
    }
});

pm.test("Comments count is correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.comments_count).to.be.at.least(1);
});
```

### 5. Получение детального комментария
**GET** `{{base_url}}/api/v1/comments/{{comment_id}}/`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comment details are correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.id).to.eql(pm.environment.get("comment_id"));
    pm.expect(jsonData.content).to.include("This is my first comment");
    pm.expect(jsonData.parent).to.be.null;
    pm.expect(jsonData.is_reply).to.be.false;
});

pm.test("Replies are included for main comment", function () {
    var jsonData = pm.response.json();
    if (jsonData.parent === null) {
        pm.expect(jsonData).to.have.property('replies');
        pm.expect(jsonData.replies).to.be.an('array');
        pm.expect(jsonData.replies_count).to.be.at.least(0);
    }
});
```

### 6. Получение ответов на комментарий
**GET** `{{base_url}}/api/v1/comments/{{comment_id}}/replies/`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comment replies structure is correct", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('parent_comment');
    pm.expect(jsonData).to.have.property('replies');
    pm.expect(jsonData).to.have.property('replies_count');
    pm.expect(jsonData.replies).to.be.an('array');
});

pm.test("Parent comment info is included", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.parent_comment.id).to.eql(pm.environment.get("comment_id"));
    pm.expect(jsonData.parent_comment).to.have.property('content');
    pm.expect(jsonData.parent_comment).to.have.property('author_info');
});

pm.test("Replies are correct", function () {
    var jsonData = pm.response.json();
    if (jsonData.replies.length > 0) {
        jsonData.replies.forEach(function(reply) {
            pm.expect(reply.parent).to.eql(pm.environment.get("comment_id"));
            pm.expect(reply.is_reply).to.be.true;
            pm.expect(reply).to.have.property('author_info');
        });
    }
});
```

### 7. Обновление комментария
**PATCH** `{{base_url}}/api/v1/comments/{{comment_id}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "content": "This is my updated first comment on this amazing blog post! Thank you for sharing such valuable information. I've learned a lot from it."
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comment updated successfully", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.content).to.eql("This is my updated first comment on this amazing blog post! Thank you for sharing such valuable information. I've learned a lot from it.");
    pm.expect(jsonData.id).to.eql(pm.environment.get("comment_id"));
});
```

### 8. Получение своих комментариев
**GET** `{{base_url}}/api/v1/comments/my-comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("My comments are returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("All comments belong to current user", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 0) {
        jsonData.results.forEach(function(comment) {
            pm.expect(comment.author_info.username).to.eql("testuser");
        });
    }
});

pm.test("Comments include both main and replies", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results.length).to.be.at.least(2); // основной комментарий + ответ
    
    var hasMainComment = jsonData.results.some(comment => comment.parent === null);
    var hasReplyComment = jsonData.results.some(comment => comment.parent !== null);
    
    pm.expect(hasMainComment).to.be.true;
    pm.expect(hasReplyComment).to.be.true;
});
```

### 9. Фильтрация комментариев по посту
**GET** `{{base_url}}/api/v1/comments/?post={{post_id}}`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comments filtered by post", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        jsonData.results.forEach(function(comment) {
            // Проверяем через API что комментарий принадлежит нужному посту
            pm.expect(comment).to.have.property('id');
        });
    }
});
```

### 10. Фильтрация комментариев по автору
**GET** `{{base_url}}/api/v1/comments/?author={{user_id}}`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comments filtered by author", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        jsonData.results.forEach(function(comment) {
            pm.expect(comment.author_info.username).to.eql("testuser");
        });
    }
});
```

### 11. Поиск в комментариях
**GET** `{{base_url}}/api/v1/comments/?search=amazing`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Search results are relevant", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        var foundRelevant = jsonData.results.some(comment => 
            comment.content.toLowerCase().includes('amazing')
        );
        pm.expect(foundRelevant).to.be.true;
    }
});
```

### 12. Сортировка комментариев
**GET** `{{base_url}}/api/v1/comments/?ordering=created_at`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Comments sorted by creation date ascending", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 1) {
        for (let i = 0; i < jsonData.results.length - 1; i++) {
            var date1 = new Date(jsonData.results[i].created_at);
            var date2 = new Date(jsonData.results[i + 1].created_at);
            pm.expect(date1.getTime()).to.be.at.most(date2.getTime());
        }
    }
});
```

### 13. Фильтрация только основных комментариев (без ответов)
**GET** `{{base_url}}/api/v1/comments/?parent__isnull=true`

**Headers:** (не требуется авторизация)

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Only main comments returned", function () {
    var jsonData = pm.response.json();
    if (jsonData.results.length > 0) {
        jsonData.results.forEach(function(comment) {
            pm.expect(comment.parent).to.be.null;
            pm.expect(comment.is_reply).to.be.false;
        });
    }
});
```

### 14. Мягкое удаление комментария
**DELETE** `{{base_url}}/api/v1/comments/{{comment_id}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Tests:**
```javascript
pm.test("Status code is 204", function () {
    pm.response.to.have.status(204);
});

pm.test("Comment is soft deleted", function () {
    // Проверяем что комментарий больше не отображается в активных
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/api/v1/comments/" + pm.environment.get("comment_id") + "/",
        method: 'GET'
    }, function (err, response) {
        pm.expect(response.code).to.eql(404);
    });
});
```

### 15. Создание комментария без авторизации (должно вернуть ошибку)
**POST** `{{base_url}}/api/v1/comments/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "post": {{post_id}},
    "content": "This should fail without authentication"
}
```

**Tests:**
```javascript
pm.test("Status code is 401", function () {
    pm.response.to.have.status(401);
});

pm.test("Authentication error returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('detail');
    pm.expect(jsonData.detail).to.include('credentials');
});
```

### 16. Создание комментария с невалидными данными
**POST** `{{base_url}}/api/v1/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "post": 999999,
    "content": ""
}
```

**Tests:**
```javascript
pm.test("Status code is 400", function () {
    pm.response.to.have.status(400);
});

pm.test("Validation errors returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.be.an('object');
    // Может содержать ошибки по полям post и content
});
```

### 17. Попытка редактировать чужой комментарий
**PATCH** `{{base_url}}/api/v1/comments/{{other_user_comment_id}}/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "content": "Trying to edit someone else's comment"
}
```

**Tests:**
```javascript
pm.test("Status code is 403", function () {
    pm.response.to.have.status(403);
});

pm.test("Permission denied error returned", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('detail');
});
```

### 18. Создание ответа на несуществующий комментарий
**POST** `{{base_url}}/api/v1/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "post": {{post_id}},
    "parent": 999999,
    "content": "Reply to non-existent comment"
}
```

**Tests:**
```javascript
pm.test("Status code is 400", function () {
    pm.response.to.have.status(400);
});

pm.test("Validation error for parent comment", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('parent');
});
```

### 19. Создание ответа на комментарий из другого поста
**POST** `{{base_url}}/api/v1/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "post": {{another_post_id}},
    "parent": {{comment_id}},
    "content": "Reply to comment from different post"
}
```

**Tests:**
```javascript
pm.test("Status code is 400", function () {
    pm.response.to.have.status(400);
});

pm.test("Validation error for cross-post comment", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('parent');
    pm.expect(jsonData.parent[0]).to.include('same post');
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
5. **Создание комментариев** → Сохранение comment_id и reply_comment_id
6. **Тестирование CRUD операций с комментариями**
7. **Тестирование специальных эндпоинтов комментариев**
8. **Тестирование фильтрации и поиска постов и комментариев**
9. **Тестирование специальных эндпоинтов** (популярные, последние)
10. **Тестирование ошибок и edge cases**
11. **Удаление тестовых данных**

## Дополнение к настройкам окружения для комментариев

Добавьте в переменные окружения:
- `user_id`: (ID текущего пользователя, можно получить из профиля)
- `reply_comment_id`: (ID ответа на комментарий)
- `other_user_comment_id`: (ID комментария другого пользователя для тестирования доступа)
- `another_post_id`: (ID другого поста для тестирования валидации)

## Удаление тестовых данных

### Удаление комментариев (мягкое удаление)
**DELETE** `{{base_url}}/api/v1/comments/{{reply_comment_id}}/`

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

### Тест пагинации для комментариев
**GET** `{{base_url}}/api/v1/comments/?page=1&page_size=5`

**Tests:**
```javascript
pm.test("Comments pagination works correctly", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('count');
    pm.expect(jsonData).to.have.property('next');
    pm.expect(jsonData).to.have.property('previous');
    pm.expect(jsonData.results.length).to.be.at.most(5);
});
```

### Тест комбинированной фильтрации комментариев
**GET** `{{base_url}}/api/v1/comments/?post={{post_id}}&search=comment&ordering=-created_at`

**Tests:**
```javascript
pm.test("Combined comment filtering works", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        // Проверяем что результаты содержат искомое слово
        var foundRelevant = jsonData.results.some(comment => 
            comment.content.toLowerCase().includes('comment')
        );
        pm.expect(foundRelevant).to.be.true;
    }
});
```

### Тест структуры вложенных комментариев
**GET** `{{base_url}}/api/v1/comments/post/{{post_id}}/`

**Tests:**
```javascript
pm.test("Nested comments structure is correct", function () {
    var jsonData = pm.response.json();
    if (jsonData.comments.length > 0) {
        var mainComment = jsonData.comments.find(comment => comment.parent === null);
        if (mainComment && mainComment.replies.length > 0) {
            mainComment.replies.forEach(function(reply) {
                pm.expect(reply.parent).to.eql(mainComment.id);
                pm.expect(reply.is_reply).to.be.true;
                pm.expect(reply).to.have.property('author_info');
                pm.expect(reply).to.have.property('created_at');
            });
        }
    }
});
```

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
5. Создание комментариев и ответов
6. Получение и фильтрация комментариев
7. Обновление постов и комментариев
8. Специальные эндпоинты
9. Тестирование ошибок и валидации
10. Удаление тестовых данных
11. Выход из системы

## Дополнительные URL для комментариев

Не забудьте добавить в ваш `config/urls.py`:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/posts/', include('apps.main.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/comments/', include('apps.comments.urls')),  # Добавить эту строку
]
```

Это руководство поможет вам протестировать все функции вашего блог API включая новое приложение комментариев и убедиться в их корректной работе.