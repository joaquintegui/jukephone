#!/bin/bash
# Correr UNA VEZ en la Pi para configurar todo.
# Uso: bash pi-setup.sh <GITHUB_RUNNER_TOKEN>
#
# El token se obtiene en:
# GitHub repo → Settings → Actions → Runners → New self-hosted runner
# Copiá el token que aparece en el paso "Configure" (empieza con "A")

set -e

REPO_URL="https://github.com/joaquintegui/jukephone"
RUNNER_TOKEN="${1:?Pasá el token como argumento: bash pi-setup.sh <TOKEN>}"
RUNNER_DIR="$HOME/actions-runner"

# ── 1. Instalar el runner ────────────────────────────────────────────────────
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    RUNNER_PKG="actions-runner-linux-arm64-2.321.0.tar.gz"
else
    RUNNER_PKG="actions-runner-linux-arm-2.321.0.tar.gz"
fi

echo "Descargando GitHub Actions runner ($ARCH)..."
curl -sSfL "https://github.com/actions/runner/releases/download/v2.321.0/${RUNNER_PKG}" \
    -o runner.tar.gz
tar xzf runner.tar.gz
rm runner.tar.gz

# Configurar runner con label "jukephone"
./config.sh \
    --url "$REPO_URL" \
    --token "$RUNNER_TOKEN" \
    --name "jukephone-pi" \
    --labels "jukephone" \
    --work "_work" \
    --unattended

# Instalar como servicio systemd
sudo ./svc.sh install
sudo ./svc.sh start

echo "✓ Runner instalado y corriendo"

# ── 2. Instalar servicio jukephone ───────────────────────────────────────────
cd ~/jukephone

sudo cp jukephone.service /etc/systemd/system/jukephone.service
sudo systemctl daemon-reload
sudo systemctl enable jukephone
sudo systemctl start jukephone

echo "✓ Servicio jukephone instalado y activo"

# ── 3. Permitir que el runner reinicie el servicio sin contraseña ────────────
SUDOERS_LINE="joaquin ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart jukephone, /usr/bin/systemctl stop jukephone, /usr/bin/systemctl start jukephone"
echo "$SUDOERS_LINE" | sudo tee /etc/sudoers.d/jukephone > /dev/null
sudo chmod 440 /etc/sudoers.d/jukephone

echo "✓ Sudoers configurado"
echo ""
echo "Todo listo. Flujo de deploy:"
echo "  git push origin main  →  Pi hace git pull + reinicia servicio automáticamente"
