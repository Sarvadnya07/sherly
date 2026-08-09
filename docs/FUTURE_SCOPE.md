# Future Scope & Roadmap

Sherly is continuously evolving. This document outlines the short-term and long-term roadmap for the project, focusing on scalability, agentic capabilities, and deployment.

## 🚀 Short-Term Improvements (Next 3-6 Months)

1. **Enhanced Visual UI Debugger**
   - Provide a visual tree of the DOM/Desktop UI for the agent to inspect.
   - Allow Sherly to visually highlight the exact lines of code it plans to change directly within the IDE, rather than just in the Sherly PySide6 app.

2. **Multi-Agent Swarm (MAS)**
   - Transition from a single orchestrator to a multi-agent system.
   - Example: A `Planner Agent` breaks down a task, a `Coder Agent` writes the code, and a `QA Agent` runs tests before presenting the final patch to the user.

3. **Expanded Cloud Fallbacks (Opt-In)**
   - While Sherly is local-first, we will add support for OpenAI/Anthropic APIs for users who explicitly opt-in and require heavier reasoning models than their local hardware supports.

## 📈 Long-Term Roadmap (6-12 Months)

1. **Full Workspace Autonomy**
   - Implement persistent background monitoring. Sherly can proactively suggest fixes when a test suite fails in the background or a linter throws an error, without being explicitly invoked.

2. **Custom Skill & Plugin Ecosystem**
   - Open up the `plugins/` directory to allow the community to build custom deterministic tools and share them via a central registry.
   - E.g., A dedicated `Kubernetes` plugin to let Sherly interact with clusters safely.

3. **DevOps & CI/CD Evolution**
   - Deploy Sherly as a GitHub Action or GitLab CI runner that reviews PRs deterministically using the exact same safety constraints used locally.

## 🤖 AI / Automation Opportunities

- **Self-Healing Tests**: Allow Sherly to not just write tests, but automatically update brittle tests when UI/API contracts change.
- **Contextual Pre-Fetching**: Use smaller models (like Llama 3 8B) to pre-fetch relevant files into context *while* the user is typing or speaking, drastically reducing time-to-first-token.
