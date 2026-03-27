import sqlalchemy
import logging
from flask_security import (
    current_user
)

from server.db.model import OAuth2Token, db

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def authorize_user():
    return {
        "authorized": "yes"
    }

def authlib_token_update(
    name: str,
    token: dict,
    refresh_token: str = None,
    access_token: str = None
) -> dict | None:
    """Update an OAuth2 token in the database.

    This method is an Authlib construct, see Authlib documentation for more
    information.

    :param name: The name of the remote provider.
    :param token: The new token data.
    :param refresh_token: The refresh token to match.
    :param access_token: The access token to match.
    :return: The updated token as a dict, or None if not found.
    :raises sqlalchemy.exc.IntegrityError: If database commit fails.

    """

    item = None

    # Find the old token in the database
    if refresh_token:
        item = OAuth2Token.query.filter_by(
            name=name, refresh_token=refresh_token
        ).first()
    elif access_token:
        item = OAuth2Token.query.filter_by(name=name, access_token=access_token).first()
    else:
        return

    # Do an in-place update from the token.
    item.from_token(token)

    db.session.add(item)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        log.error("Failed to commit updated token...")
        db.session.rollback()

    return item.to_token()


def authlib_fetch_token(name: str) -> dict | None:
    """Fetch a token from the database.

    This method is an Authlib construct, see Authlib documentation for more
    information.

    Fetch a token from the database to refresh or initialize a new session for
    the signe-in user.

    :param name: The name of the remote to refresh or initialize the new
        session for.
    :return: The token as a dict, or None if not found.

    """

    log.info("Fetching token for [%s].", name)

    user_id = current_user.id

    item = OAuth2Token.query.filter_by(
        name=name,
        user_id=user_id,
    ).first()

    if item:
        return item.to_token()

    log.warning("Failed to fetch token for [%s].", name)

