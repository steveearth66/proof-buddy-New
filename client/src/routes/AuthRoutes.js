import React from 'react';
import { Route } from 'react-router-dom';
import SignUp from '../pages/SignUp';
import SignUpUser from '../pages/SignUpUser';
import Login from '../pages/Login';
import Logout from '../pages/Logout';
import ForgotPassword from '../pages/ForgotPassword';
import ResetPassword from '../pages/ResetPassword';
import Proofs from "../pages/Proofs";
import Terms from '../pages/Terms';
import Term from '../pages/Term';
import { RouteWithAuth, RouteWithNoAuth } from "../utils/routeAuthUtils";

/**
 * A component that renders a group of routes related to authentication.
 *
 * @returns {React.Fragment} A fragment containing the defined routes.
 */
const AuthRoutes = () => {
  return (
    <>
      <Route path="/signup" element={<RouteWithNoAuth component={SignUp} />} />
      <Route
        path="/signup/student"
        element={<RouteWithNoAuth component={SignUpUser} role="student" />}
      />
      <Route
        path="/signup/instructor"
        element={<RouteWithNoAuth component={SignUpUser} role="instructor" />}
      />
      <Route path="/login" element={<RouteWithNoAuth component={Login} />} />
      <Route path="/logout" element={<RouteWithAuth component={Logout} />} />
      <Route
        path="/forgot-password"
        element={<RouteWithNoAuth component={ForgotPassword} />}
      />
      <Route
        path="/reset-password"
        element={<RouteWithNoAuth component={ResetPassword} />}
      />
      <Route path="/proofs" element={<RouteWithAuth component={Proofs} />} />
      <Route path="/terms" element={<RouteWithAuth component={Terms} />} />
      <Route path="/terms/:id" element={<RouteWithAuth component={Term} />} />
    </>
  );
};

export default AuthRoutes;
