#!/bin/sh
set -eu

mc alias set local "$VGOV_S3_ENDPOINT" "$VGOV_S3_ACCESS_KEY" "$VGOV_S3_SECRET_KEY"
mc mb --ignore-existing local/vgov-artifacts
mc version enable local/vgov-artifacts
mc mb --ignore-existing local/mlflow-artifacts
