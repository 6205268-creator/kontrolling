# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# Копирование package.json и установка зависимостей
COPY package.json ./
RUN npm install

# Копирование исходного кода и сборка
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копирование собранного приложения
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
