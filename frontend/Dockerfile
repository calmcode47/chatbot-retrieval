# Dockerfile.ui — DocuMind React frontend

FROM node:20-slim

WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package*.json ./

RUN npm ci

# Copy the rest of the frontend folder
COPY . .

EXPOSE 8501

# Run the Vite dev server
CMD ["npm", "run", "dev"]

