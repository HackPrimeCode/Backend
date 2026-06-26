from uuid import UUID
from fastapi_mail import MessageSchema
from src.core.email import fastmail


async def send_invite_email(
    email: str,
    token: UUID,
    title: str,
    role: str,
):
    link = f"http://localhost:5173/auth?token={token}"

    html_content = f"""
    <html>
        <body>
            <h2>Приглашение на "{title}"</h2>
            <p>Вас пригласили как <b>{role}</b>.</p>
            <p>Для продолжения перейдите по ссылке:</p>
            <a href="{link}">{link}</a>
        </body>
    </html>
    """

    message = MessageSchema(
        subject=f"Приглашение на {title}",
        recipients=[email],
        body=html_content,
        subtype="html",
    )

    await fastmail.send_message(message)