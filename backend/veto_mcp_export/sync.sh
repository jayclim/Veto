#!/bin/bash
# Sync files to VetoMCP
cp models.py ../../../VetoMCP/
cp agent_guard_migration.sql ../../../VetoMCP/
cp main.py ../../../VetoMCP/
cp tools/agent_guard_rails.py ../../../VetoMCP/tools/
cp pyproject.toml ../../../VetoMCP/

echo "Sync complete. VetoMCP updated."
