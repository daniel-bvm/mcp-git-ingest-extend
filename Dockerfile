from danieltn11/mcp-proxy:3.12_v1.0.1

copy pyproject.toml pyproject.toml
copy src src
copy config.json config.json

run pip install . && rm -rf src pyproject.toml