# Where2Watch

Self-hosted app to find the shows/movies you want to watch are available on certain providers.

```bash
git clone https://github.com/Alyetama/Where2Watch.git
cd /Where2Watch
```

```bash
docker run \
  -d --restart unless-stopped \
  -v "${PWD}"/config:/app/config \
  -p 8501:8501 \
  alyetama/w2w:latest
```
