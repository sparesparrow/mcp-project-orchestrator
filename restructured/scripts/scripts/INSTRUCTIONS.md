# Testing MCP Servers in Claude Desktop

Follow this procedure to test the MCP servers in Claude Desktop:

## Testing Procedure

1. First, initialize the PostgreSQL database:

```bash
cd /home/sparrow/mcp
./init_postgres.sh
```

2. Run the testing script:

```bash
cd /home/sparrow/mcp
./test_claude_desktop.sh
```

The test script will:
- Kill Claude Desktop if it's running
- Delete logs at `/home/sparrow/.config/Claude/logs`
- Run Claude Desktop with `~/bin/run-claude.sh`
- Wait one minute for initialization
- Kill Claude Desktop
- Check logs for errors
- Check container status

## Manual Testing (Alternative)

If you prefer to test manually:

1. Kill Claude Desktop if running:
```bash
pkill -f "Claude Desktop" || true
```

2. Delete logs:
```bash
rm -rf /home/sparrow/.config/Claude/logs/*
```

3. Run Claude Desktop:
```bash
~/bin/run-claude.sh
```

4. Wait one minute.

5. Kill Claude Desktop:
```bash
pkill -f "Claude Desktop" || true
```

6. Check logs:
```bash
grep -r "ERROR" /home/sparrow/.config/Claude/logs
```

7. Look for specific MCP server errors:
```bash
grep -r "prompt-manager-py" /home/sparrow/.config/Claude/logs | grep "ERROR"
grep -r "prompts-sse" /home/sparrow/.config/Claude/logs | grep "ERROR"
grep -r "prompts-stdio" /home/sparrow/.config/Claude/logs | grep "ERROR"
grep -r "db" /home/sparrow/.config/Claude/logs | grep "ERROR"
```

## Fixing Issues

If you encounter errors:

1. Check if the configuration files need fixes:
```bash
nano /home/sparrow/mcp/claude_desktop_config.json
```

2. Check if the source code needs fixes:
```bash
ls -la /home/sparrow/projects/mcp-prompts/
```

3. Check Docker containers:
```bash
docker ps -a | grep -E "postgres|prompt|pgai"
```

4. Check Docker logs:
```bash
docker logs mcp-postgres-db-container
docker logs mcp-prompt-manager-py
docker logs mcp-prompts-sse
docker logs mcp-prompts-stdio
```

5. Fix the identified issues and repeat the testing procedure.

## Verifying pgai and Prompts Functionality

To test if pgai is working correctly:

```bash
docker exec -it mcp-postgres-db-container psql -U postgres -c "SELECT ai.text_to_sql('How many flights arrived in Houston, TX in June 2024?');"
```

To test if prompts are working:

1. Connect to the prompt database:
```bash
docker exec -it mcp-postgres-db-container psql -U postgres -d prompts
```

2. Check the tables:
```sql
\dt
```

3. List available prompts:
```sql
SELECT * FROM prompts;
```

If everything is working correctly, you should be able to use the MCP servers from Claude Desktop. 