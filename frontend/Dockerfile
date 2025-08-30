FROM node:20-alpine AS builder

WORKDIR /app

# Копирование package.json и установка всех зависимостей
COPY package*.json ./
RUN npm install

# Копирование исходного кода и сборка
COPY . .
RUN npm run build

# Production стадия с nginx
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование кастомной конфигурации nginx для SPA
# Важно: Конфигурация Nginx теперь находится в корне проекта
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]