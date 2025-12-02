# MCP Project Orchestrator

## Project Overview
MCP Project Orchestrator is a modular service orchestration framework based on the Model Context Protocol (MCP). It provides tooling for managing multi-service deployments with automated task scheduling and inter-service communication.

## Status
This repo is currently transitioning away from MCP-centric design toward modular, lightweight alternatives. See [MIA](https://github.com/sparesparrow/mia) for the newer Lean ZeroMQ+FlatBuffers architecture.

## Maintenance Mode
- **Preservation**: Core orchestration logic archived for reference
- **Active Development**: Focus has shifted to single-box solutions (MIA) rather than multi-service orchestration
- **Future Use**: May be resurrected for advanced multi-device scenarios

## Tasks (If Reactivation Needed)

### Phase 1: Modernization
- [ ] Evaluate MCP v2.x compatibility
- [ ] Assess Lean ZeroMQ integration possibility
- [ ] Document breaking changes vs. MIA approach

### Phase 2: Legacy Support (Optional)
- [ ] Maintain compatibility layer for existing deployments
- [ ] Provide migration guides to MIA for new projects
- [ ] Archive comprehensive documentation

## Key Files
- `src/`: Orchestration service code
- `schemas/`: MCP protocol schemas (legacy)
- `tests/`: Test suite
- `docs/`: Architecture and usage documentation

## Deprecation Notes
- **Recommended for New Projects**: Use MIA instead
- **Existing Deployments**: Continue using current version; support available via issues
- **Archive Status**: Code preserved for historical reference and potential future reactivation

## Contributors
- Maintenance: TBD

## See Also
- [MIA - Lean IoT Assistant](https://github.com/sparesparrow/mia)
- [SpareTools - DevOps Tooling](https://github.com/sparesparrow/sparetools)
