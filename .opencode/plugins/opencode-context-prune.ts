export default {
  name: "opencode-context-prune",
  version: "1.0.0",
  description: "Prunes obsolete tool outputs from session context to save tokens",
  hooks: {
    sessionIdle: (ctx) => {
      // Minimal safe pruning: trims long outputs without removing essential instructions
      if (ctx && ctx.history && Array.isArray(ctx.history)) {
        ctx.history = ctx.history.map(item => {
          if (item && item.content && typeof item.content === "string" && item.content.length > 8000) {
            return { ...item, content: item.content.slice(0, 4000) + " [pruned for token efficiency]" };
          }
          return item;
        });
      }
    },
  },
};
