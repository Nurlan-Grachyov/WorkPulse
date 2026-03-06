from src.domain.comments.repositories import CommentRepository


class CommentService:
    def __init__(self, evaluation: CommentRepository):
        self._evaluation = evaluation
