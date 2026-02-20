FROM node:24-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Set environment variable during build
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

CMD ["npm", "start"]
