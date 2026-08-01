#!/usr/bin/env bash
set -euo pipefail

VERSION="4.5.12"
BASE_URL="https://download.blender.org/release/Blender4.5"
ARCHIVE="blender-${VERSION}-linux-x64.tar.xz"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="${ROOT}/.tools/blender"
INSTALL_DIR="${TOOLS_DIR}/${VERSION}"
CACHE_DIR="${ROOT}/.cache/blender"
REPORT_DIR="${ROOT}/artifacts/blender_reports"

mkdir -p "${TOOLS_DIR}" "${CACHE_DIR}" "${REPORT_DIR}"

if [[ ! -x "${INSTALL_DIR}/blender" ]]; then
  command -v curl >/dev/null || { echo "curl não encontrado" >&2; exit 2; }
  command -v sha256sum >/dev/null || { echo "sha256sum não encontrado" >&2; exit 2; }
  command -v tar >/dev/null || { echo "tar não encontrado" >&2; exit 2; }

  curl --fail --location --retry 3 --output "${CACHE_DIR}/${ARCHIVE}" "${BASE_URL}/${ARCHIVE}"
  curl --fail --location --retry 3 --output "${CACHE_DIR}/blender-${VERSION}.sha256" "${BASE_URL}/blender-${VERSION}.sha256"

  expected="$(awk -v file="${ARCHIVE}" '$2 == file {print $1}' "${CACHE_DIR}/blender-${VERSION}.sha256")"
  [[ "${expected}" =~ ^[0-9a-fA-F]{64}$ ]] || { echo "Checksum oficial não encontrado" >&2; exit 3; }
  actual="$(sha256sum "${CACHE_DIR}/${ARCHIVE}" | awk '{print $1}')"
  [[ "${actual}" == "${expected}" ]] || { echo "SHA-256 inválido" >&2; exit 4; }

  tmp="${TOOLS_DIR}/.extract-${VERSION}"
  rm -rf "${tmp}" "${INSTALL_DIR}"
  mkdir -p "${tmp}"
  tar -xJf "${CACHE_DIR}/${ARCHIVE}" -C "${tmp}" --strip-components=1
  mv "${tmp}" "${INSTALL_DIR}"
fi

ln -sfn "${INSTALL_DIR}" "${TOOLS_DIR}/current"
"${INSTALL_DIR}/blender" --version
"${INSTALL_DIR}/blender" \
  --background \
  --factory-startup \
  --disable-autoexec \
  --python-exit-code 1 \
  --python "${ROOT}/blender_env/scripts/verify_environment.py" \
  -- --expected-version "${VERSION}" --report "${REPORT_DIR}/environment_linux.json"

"${INSTALL_DIR}/blender" \
  --background \
  --factory-startup \
  --disable-autoexec \
  --python-exit-code 1 \
  --python "${ROOT}/blender_env/scripts/create_roblox_workspace.py" \
  -- "${ROOT}/artifacts/ROBLOX_CONTRACT_WORKSPACE_4_5.blend"

echo "Ambiente Blender pronto em ${INSTALL_DIR}"
