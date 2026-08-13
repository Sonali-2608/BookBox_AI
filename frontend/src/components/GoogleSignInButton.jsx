import { GoogleLogin } from "@react-oauth/google";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

/**
 * Wraps @react-oauth/google's GoogleLogin: it hands us a Google ID token
 * (credential) directly, which we forward to POST /api/auth/google. No
 * redirect/callback route needed.
 */
export default function GoogleSignInButton({ redirectTo = "/dashboard", className = "" }) {
  const { loginWithGoogleCredential } = useAuth();
  const navigate = useNavigate();

  return (
    <div className={className}>
      <GoogleLogin
        onSuccess={async (credentialResponse) => {
          if (!credentialResponse.credential) return;
          try {
            await loginWithGoogleCredential(credentialResponse.credential);
            navigate(redirectTo);
          } catch {
            // Error state is surfaced via useAuth().error where this
            // button is rendered.
          }
        }}
        onError={() => {
          /* handled via useAuth().error in the consuming page */
        }}
        theme="filled_black"
        shape="pill"
        text="signin_with"
      />
    </div>
  );
}
