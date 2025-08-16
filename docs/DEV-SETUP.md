### Frontend (web_ui/client) Node version

We require Node 20 LTS for local dev and Docker parity.

Install via nvm:
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    nvm install 20
    nvm use 20

After changing dependencies, regenerate the lockfile on Linux:
    cd web_ui/client
    rm -rf node_modules package-lock.json
    npm install
    git add package-lock.json && git commit -m "regen lockfile on Linux"

Common error:
    SyntaxError: Unexpected token '.'
Cause: Node <14 in WSL. Fix by using Node 20 as above.

For steps to rebuild the project and Docker images during active development, see the [Fast Development Guide](FAST-DEVELOPMENT.md).
