from starlette.config import Config

config = Config(".env")

# OAuth2 provider configurations
OAUTH_PROVIDERS = {
    'google': {
        'client_id': config("GOOGLE_CLIENT_ID"),
        'client_secret': config("GOOGLE_CLIENT_SECRET"),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'access_token_url': 'https://accounts.google.com/o/oauth2/token',
        'redirect_uri': 'http://localhost:8000/auth/google/callback',
        'scope': 'openid profile email'
    },
    'facebook': {
        'client_id': config("FACEBOOK_CLIENT_ID"),
        'client_secret': config("FACEBOOK_CLIENT_SECRET"),
        'authorize_url': 'https://www.facebook.com/dialog/oauth',
        'access_token_url': 'https://graph.facebook.com/v10.0/oauth/access_token',
        'redirect_uri': 'http://localhost:8000/auth/facebook/callback',
        'scope': 'email public_profile'
    },
    # Add other providers here...
}
