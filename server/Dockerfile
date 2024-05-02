FROM node:22-alpine

WORKDIR /server

COPY package*.json ./

RUN npm install --omit=dev

COPY . .

CMD [ "npm", "start" ]