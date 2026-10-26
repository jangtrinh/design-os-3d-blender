# Minimal image to run the DESIGN:OS 3D Blender MCP server over stdio
# (used by MCP directories such as Glama to introspect tools).
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY knowledge ./knowledge
COPY specs ./specs
RUN pip install --no-cache-dir .
ENTRYPOINT ["design-os-3d-blender"]
