FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM alpine:3.19
COPY --from=build /app/dist /dist
CMD ["cp", "-r", "/dist/.", "/output/"]
