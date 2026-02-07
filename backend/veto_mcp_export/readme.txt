AUTOMATED VETO MCP EXPORT

This directory contains the updated files needed for the `VetoMCP` repository to support Agent Guard Rails.
Since I don't have write access to `VetoMCP`, please copy these files manually:

1. Copy `agent_guard_migration.sql` to `VetoMCP/` and run it in Supabase SQL Editor.
   cp agent_guard_migration.sql ../../../VetoMCP/

2. Copy `models.py` to `VetoMCP/`.
   cp models.py ../../../VetoMCP/

3. Copy `tools/agent_guard_rails.py` to `VetoMCP/tools/`.
   cp tools/agent_guard_rails.py ../../../VetoMCP/tools/

4. Replace `VetoMCP/main.py` with `main.py` from this folder.
   cp main.py ../../../VetoMCP/

Or simply run:
cp -R * ../../../VetoMCP/
