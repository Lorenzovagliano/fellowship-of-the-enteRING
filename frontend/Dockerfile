FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV VITE_API_URL=http://localhost:8000

EXPOSE 8080

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
