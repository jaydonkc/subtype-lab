FROM node:22-slim

WORKDIR /app
COPY apps/web/package.json /app/package.json
RUN npm install
COPY apps/web /app
ENV ANALYSIS_API_PROXY=http://analysis-engine:8000
EXPOSE 3000
CMD ["npm", "run", "dev"]
