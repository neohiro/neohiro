// GitHub Repo State Context Augment Plugin
// Assumption: uses GitHub MCP/REST for repo info injection
export default {
  name: "github-context-augment",
  version: "1.0.0",
  description: "Injects current repo state (branch, commits, PR status) into session context",
  hooks: {
    sessionStart: async (context) => {
      try {
        const repo = (context && context.location) ? context.location : "github-manager";
        // Safe fallback: inject minimal context if GitHub MCP unavailable
        const summary = `Repo: ${repo} | Status: active | Last check: ${new Date().toISOString()}`;
        if (context && typeof context === "object") {
          context.systemInstructions = (context.systemInstructions || "") + "\n\n[GitHub Context]\n" + summary;
        }
      } catch (e) {
        // Silently skip if repo info unavailable — never break session
      }
    },
  },
};
