# Phase 5: MCP Wrapper

## Goal
Wrap core documentation capabilities as MCP-compatible tools with secure token-gated access and predictable tool contracts.

## Inputs From Master Plan
- FastMCP integration
- MCP access domain (`mcp.domain`)
- MCP token requirement (`MCP_SERVER_TOKEN`)
- Core capabilities: list docs, browse sections, read content, tree view, semantic search

## Scope
- MCP server bootstrap and registration
- Tool definitions and parameter schemas
- Mapping between MCP tool calls and internal service APIs
- Authentication and rate limiting for MCP-facing routes
- Consistent error translation from backend exceptions to MCP responses

## Development Plan
1. Add MCP module and initialize FastMCP server entrypoint.
2. Implement tools:
   - `list_documentations`
   - `list_documentation_sections`
   - `get_section_content`
   - `get_documentation_tree`
   - `search_documentation`
3. Define strict tool parameter and response schemas.
4. Add token auth middleware for MCP access.
5. Add rate limiting and request tracing for MCP requests.
6. Map internal exceptions to stable MCP error messages.
7. Add MCP health and readiness checks.
8. Document tool contracts and sample invocations.

## Unit Testing Plan
1. Tool contract tests for each MCP tool (valid inputs and edge cases).
2. Auth tests for missing/invalid tokens.
3. Error-mapping tests for not found, invalid section path, and backend failures.
4. Schema compliance tests for response payloads.
5. Rate limit behavior tests under burst traffic.

## Manual Testing Plan
1. Connect from an MCP client with valid token and execute each tool.
2. Verify invalid token attempts are rejected with expected error codes.
3. Test section pagination and deep tree retrieval on large docs.
4. Run semantic queries and validate returned content snippets.
5. Trigger backend failure scenario and verify MCP responses remain readable.

## Exit Criteria
- MCP clients can discover and use all documentation tools.
- Security controls are enforced consistently.
- Tool contracts are documented and stable.

## Deliverables
- MCP server module
- Tool registration and schemas
- Auth/rate-limit middleware
- MCP integration tests and docs
