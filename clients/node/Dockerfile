FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY prisma ./prisma
COPY prisma.config.ts ./
RUN DATABASE_URL=postgresql://unused@localhost/unused npx prisma generate
COPY *.mjs ./
ENTRYPOINT ["node"]
