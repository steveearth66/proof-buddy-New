FROM node:alpine as builder


WORKDIR /client

COPY package.json .

RUN npm install -f


COPY . .

ARG REACT_APP_BACKEND_API_BASE_URL

ENV REACT_APP_BACKEND_API_BASE_URL=$REACT_APP_BACKEND_API_BASE_URL

RUN npm run build


FROM nginx:alpine

WORKDIR /usr/share/nginx/html

RUN rm -rf ./*

COPY --from=builder /client/build .

ENTRYPOINT [ "nginx", "-g", "daemon off;" ]

EXPOSE 80:80