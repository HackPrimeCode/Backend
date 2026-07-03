from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from src.api.deps import DbSession
from src.core.config import settings
from src.core.cookies import delete_refresh_token_cookie, set_refresh_token_cookie
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from src.enums import GlobalRole
from src.models.user import User
from src.models.team import Team
from src.models.invite_token import InviteToken
from src.schemas.auth import (
    AuthResponse,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
    InviteExchangeRequest,
    InviteExchangeResponse,
    PendingInvite)

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(db: DbSession, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _issue_auth_response(user: User, response: Response) -> AuthResponse:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    set_refresh_token_cookie(response, refresh_token)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, response: Response, db: DbSession) -> AuthResponse:
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        global_role=GlobalRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_auth_response(user, response)


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, response: Response, db: DbSession) -> AuthResponse:
    user = _authenticate_user(db, payload.email.lower(), payload.password)
    return _issue_auth_response(user, response)


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    user = _authenticate_user(db, form_data.username.lower(), form_data.password)
    refresh_token = create_refresh_token(str(user.id))
    set_refresh_token_cookie(response, refresh_token)
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer",
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh_session(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias=settings.REFRESH_COOKIE_NAME)] = None,
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    user_id = decode_refresh_token(refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return _issue_auth_response(user, response)

@router.post("/exchange", response_model=InviteExchangeResponse)
def exchange_invite_token(
    payload: InviteExchangeRequest,
    db: DbSession,
):
    invite = db.scalar(
        select(InviteToken).where(InviteToken.token == payload.token)
    )

    if invite is None or invite.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used token",
        )

    user = db.scalar(
        select(User).where(User.email == invite.email)
    )

    if user is None:
        user = User(
            email=invite.email,
            name=None,
        )
        db.add(user)
        db.flush()

    access_token = create_access_token(user.id)

    team_name = None
    if invite.target_team_id:
        team = db.get(Team, invite.target_team_id)
        if team:
            team_name = team.name

    return InviteExchangeResponse(
        access_token=access_token,
        pending_invite=PendingInvite(
            invite_id=invite.token,
            hackathon_id=invite.hackathon_id,
            team_name=team_name,
            target_role=invite.target_role.value,
        ),
    )


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    delete_refresh_token_cookie(response)
    return {"detail": "Successfully logged out"}
