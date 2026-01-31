/**
 * A simplified logging utility for the application.
 */

const isProduction = process.env.REACT_APP_NODE_ENV === 'production';

const formatMessage = (level, message) => {
  const timestamp = new Date().toISOString().replace(/T/, ' ').replace(/\..+/, '');
  return `${timestamp} [${level.toUpperCase()}]: ${message}`;
};

const log = (level, message, ...additionalDetails) => {
  if (isProduction) return; // Skip logging in production
  
  const formattedMessage = formatMessage(level, message);
  const details = additionalDetails.map(detail =>
    detail instanceof Error ? detail.stack : detail
  );
  
  console[level](formattedMessage, ...details);
};

const logger = {
  info: (message, ...details) => log('log', message, ...details),
  warn: (message, ...details) => log('warn', message, ...details),
  error: (message, ...details) => log('error', message, ...details),
  debug: (message, ...details) => log('debug', message, ...details)
};

export default logger;
