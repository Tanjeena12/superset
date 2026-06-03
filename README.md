# Devin Event-Driven Remediation Engine

This automation engine monitors GitHub issues for specific remediation tags and programmatically spins up Devin AI architectures to patch code-quality vulnerabilities autonomously.

## How to Run (Using Docker)

1. Build the Docker image:
```bash
docker build -t devin-automation .