FROM node:18 AS builder

WORKDIR /app

COPY ["package.json","package-lock.json","/app/"]

RUN npm install

RUN npm install -g @angular/cli

COPY . /app

RUN ng build

EXPOSE 4200

CMD ["ng", "serve", "--host", "0.0.0.0", "--port", "4200"]
