# Stage 1: Build environment
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependency configuration files
COPY package*.json ./

# Clean install of npm packages
RUN npm ci

# Copy the rest of the application files
COPY . .

# Build-time environment variable to map client-side api router
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the Next.js application
RUN npm run build

# Stage 2: Runtime environment
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built bundles, static assets, and package dependencies from builder stage
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Expose Next.js port
EXPOSE 3000

# Start Next.js production server
CMD ["npm", "run", "start"]
