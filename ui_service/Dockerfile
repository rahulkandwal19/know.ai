# Use Node.js Debian base image
FROM node:22-trixie

WORKDIR /app

# Copy only package files first (better caching)
COPY package*.json ./

# Install dependencies inside container
RUN npm install

# Copy the rest of your source code
COPY . .

EXPOSE 5173

# Start Vite dev server
CMD ["npm", "run", "dev", "--", "--host"]
