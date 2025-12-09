#!/bin/bash
# run.sh
cd ..
APP_MODULE="mineru_svr.main:app"
PORT=8091
WORKERS=1
uvicorn "$APP_MODULE" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers $WORKERS \
    --log-level info