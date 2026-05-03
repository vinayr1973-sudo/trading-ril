FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY trading_ril ./trading_ril
COPY mcp_server ./mcp_server
RUN pip install --no-cache-dir .
ENV PORT=8080
ENV MCP_TRANSPORT=streamable-http
EXPOSE 8080
CMD ["trading-ril-server"]
