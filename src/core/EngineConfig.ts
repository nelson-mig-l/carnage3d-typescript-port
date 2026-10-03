export interface EngineConfig {
  targetFps: number;
  fixedTimeStep: number;
  renderScale: number;
  enableDebugOverlay: boolean;
}

export const DEFAULT_ENGINE_CONFIG: EngineConfig = {
  targetFps: 60,
  fixedTimeStep: 1 / 60,
  renderScale: 1,
  enableDebugOverlay: false,
};

export function createEngineConfig(config: Partial<EngineConfig> = {}): EngineConfig {
  return {
    ...DEFAULT_ENGINE_CONFIG,
    ...config,
  };
}
