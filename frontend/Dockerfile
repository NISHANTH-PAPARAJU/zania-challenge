# Stage 1: Build the React app
FROM node:18 as build-stage

# Set the working directory
WORKDIR /app

# Copy `package.json` and `package-lock.json`
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app files
COPY . .

# Build the React app for production
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine as production-stage

# Copy the build files to the Nginx directory
COPY --from=build-stage /app/build /usr/share/nginx/html

# Expose the Nginx port
EXPOSE 80

# Run Nginx
CMD ["nginx", "-g", "daemon off;"]
