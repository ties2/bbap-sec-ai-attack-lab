#!/usr/bin/env sh
set -eu

REPO_URL="${BBAP_KNOWLEDGE_HUB_REPO:-https://github.com/ties2/BBAP-Sec-Knowledge-Hub.git}"
BRANCH="${BBAP_KNOWLEDGE_HUB_BRANCH:-main}"
TARGET_DIR="${BBAP_KNOWLEDGE_HUB_PATH:-external/BBAP-Sec-Knowledge-Hub}"

if [ -d "${TARGET_DIR}/.git" ]; then
  echo "[sync] Updating knowledge hub in ${TARGET_DIR}"
  git -C "${TARGET_DIR}" fetch origin "${BRANCH}" --depth 1
  git -C "${TARGET_DIR}" checkout "${BRANCH}"
  git -C "${TARGET_DIR}" pull --ff-only origin "${BRANCH}"
else
  echo "[sync] Cloning knowledge hub to ${TARGET_DIR}"
  mkdir -p "$(dirname "${TARGET_DIR}")"
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${TARGET_DIR}"
fi

echo "[sync] Done. Source: ${REPO_URL} (${BRANCH})"
