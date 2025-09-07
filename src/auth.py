import streamlit as st

def _normalize_email(email: str) -> str:
    """
    Normalizes an email address by making it lowercase and removing periods
    from the local part (before the @).
    
    Example: 'Jane.Doe@gmail.com' -> 'janedoe@gmail.com'
    """
    if '@' not in email:
        return email.lower()
    
    local_part, domain = email.split('@', 1)
    normalized_local = local_part.replace('.', '')
    return f"{normalized_local.lower()}@{domain.lower()}"

def is_email_allowed(user_email: str) -> bool:
    """
    Checks if a user's email is in the allowed list defined in secrets.toml.
    Performs normalization to be case-insensitive and ignore periods.
    
    If the [allowed_emails] section is not in secrets.toml, this function
    will default to allowing all users to maintain original functionality.
    """
    try:
        allowed_emails_raw = st.secrets["allowed_emails"]["emails"]
        if not isinstance(allowed_emails_raw, list):
            st.warning("Configuration issue: `allowed_emails.emails` in secrets.toml is not a list of strings. No users can register.")
            return False
    except (KeyError, FileNotFoundError):
        # If the secret is not defined, allow everyone to register as a fallback.
        # This maintains original functionality if the feature isn't configured.
        return True

    normalized_allowed_list = [_normalize_email(email) for email in allowed_emails_raw]
    normalized_user_email = _normalize_email(user_email)
    
    return normalized_user_email in normalized_allowed_list
