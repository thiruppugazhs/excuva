// neon.ts - Neon Infrastructure, Lakebase Postgres & Cloud Object Storage Configuration
import { defineConfig } from "@neon/config/v1";

export default defineConfig({
  preview: {
    // S3-compatible cloud object storage bucket for generated proof documents & attachments
    buckets: {
      "excuseai-documents": {
        access: "private",
      },
    },
  },
  branch: (branch) => {
    return {
      postgres: {
        computeSettings: {
          autoscalingLimitMinCu: 0.25,
          autoscalingLimitMaxCu: 1,
          suspendTimeout: "5m",
        },
      },
    };
  },
});
