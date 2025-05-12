FROM node:18-alpine

# Create a non-root user for security
RUN addgroup app && adduser -S -G app app

WORKDIR /app

COPY package*.json ./

RUN npm install --production

COPY . .

USER app

EXPOSE 3000

CMD ["node", "index.js"]