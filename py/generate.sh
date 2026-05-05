for src in "$@"; do
uv run python secspider_tool.py pack --input $src
done
