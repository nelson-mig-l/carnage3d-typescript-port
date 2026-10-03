/**
 * Example usage:
 *
 *   import { logger } from './core/Logger';
 *
 *   logger.info('Game started');
 *   logger.debug('Player spawned', { id: player.id });
 *   logger.warn('Asset missing', { path });
 *   logger.error('Renderer failed', { error });
 *
 * Keep game code dependent on this logger instead of console.* so the
 * implementation can later be replaced with Pino or another logger.
 */

export type LogContext = Record<string, unknown>;

export interface Logger {
  debug(message: string, context?: LogContext): void;
  info(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
  error(message: string, context?: LogContext): void;
}

class ConsoleLogger implements Logger {
  debug(message: string, context?: LogContext): void {
    console.debug('[DEBUG]', message, context ?? '');
  }

  info(message: string, context?: LogContext): void {
    console.info('[INFO]', message, context ?? '');
  }

  warn(message: string, context?: LogContext): void {
    console.warn('[WARN]', message, context ?? '');
  }

  error(message: string, context?: LogContext): void {
    console.error('[ERROR]', message, context ?? '');
  }
}

export const logger: Logger = new ConsoleLogger();
