# OPTIONAL sandbox (not the default; Copilot is). Cloud Run Job per build iteration.
# Choose the coding agent per your licensing:
#   - Gemini CLI (continues under Gemini Code Assist Standard/Enterprise licences)
#   - Antigravity CLI (Google's forward path)
FROM node:22-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates python3 \
    && rm -rf /var/lib/apt/lists/*
# Pin an exact version once chosen, e.g. npm install -g @google/gemini-cli@<version>
# RUN npm install -g @google/gemini-cli@X.Y.Z
RUN useradd -m agent
USER agent
WORKDIR /work
COPY --chown=agent runner/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
