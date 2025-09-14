"""
Session management for stable browser session identification.

Creates and maintains a stable session ID (sid) that survives browser refreshes
by storing it in URL query parameters. This enables Redis-backed persistence
to maintain conversation history across page reloads and server restarts.

Note: This approach uses URL query parameters for educational purposes.
In production, you'd typically use HttpOnly cookies managed by a backend service.
"""

import uuid


def get_or_create_sid(st) -> str:
    """
    Get or create a stable session ID that survives browser refreshes.

    Uses URL query parameters to persist the session ID across page reloads.
    This triggers exactly one rerun when setting the query param for the first time.

    Args:
        st: Streamlit module (for accessing query_params and session_state)

    Returns:
        str: Stable session ID (32-character hex string)
    """
    # Read existing sid from query parameters
    qp = dict(st.query_params)
    sid = qp.get("sid")

    if not sid:
        # Generate new sid and set in query params (triggers one rerun)
        sid = uuid.uuid4().hex
        st.query_params["sid"] = sid

    # Also store in session state for quick access
    st.session_state.setdefault("sid", sid)

    return sid
