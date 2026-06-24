FROM node:20-alpine

WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npm run build

USER app

EXPOSE 3000

CMD ["npm", "run", "start"]

