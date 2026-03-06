from src.infrastructure.db.models.db_comment import Comment


def update_comment_fields(comment: Comment, fields: dict) -> Comment:
    for field, value in fields.items():
        if value is None:
            continue
        if hasattr(comment, field):
            setattr(comment, field, value)
    return comment
