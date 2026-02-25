# Этап сборки React
FROM node:21.7.1-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . ./
RUN npm run build