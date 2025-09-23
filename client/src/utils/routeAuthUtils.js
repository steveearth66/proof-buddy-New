import React from 'react';
import withAuth from '../hoc/withAuth';
import withNoAuth from '../hoc/withNoAuth';

/**
 * RouteWithAuth wraps a component with authentication logic.
 * Redirects to login if user is not authenticated.
 */
const RouteWithAuth = ({ component: Component }) => {
  const WrappedComponent = withAuth(Component);
  return <WrappedComponent />;
};

/**
 * RouteWithNoAuth wraps a component to only allow unauthenticated users.
 * Redirects authenticated users away from the component.
 */
const RouteWithNoAuth = ({ component: Component, ...rest }) => {
  const WrappedComponent = withNoAuth(Component);
  return <WrappedComponent {...rest} />;
};

export { RouteWithAuth, RouteWithNoAuth };
