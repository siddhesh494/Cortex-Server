class UserAlreadyExistsException(Exception):

    def __init__(self):

        self.message = "Email already exists."


class InvalidCredentialsException(Exception):

    def __init__(self):

        self.message = "Invalid email or password."


class UnauthorizedException(Exception):

    def __init__(self):

        self.message = "Unauthorized."


class ChatNotFoundException(Exception):

    def __init__(self):

        self.message = "Chat session not found."


class DocumentAlreadyUploadedException(Exception):

    def __init__(self):
        self.message = (
            "A document has already been uploaded for this chat session. "
            "Only one document is allowed per session."
        )


class UnsupportedFileTypeException(Exception):

    def __init__(self, filename: str | None = None):
        suffix = f" ({filename})" if filename else ""
        self.message = (
            f"Unsupported file type{suffix}. "
            "Only PDF (.pdf) and text (.txt) files are allowed."
        )


class EmptyDocumentException(Exception):

    def __init__(self):
        self.message = "The uploaded document contains no readable text."


class RagIndexingException(Exception):

    def __init__(self, detail: str = "Failed to index the uploaded document."):
        self.message = detail


class PortfolioSessionNotFoundException(Exception):

    def __init__(self):
        self.message = (
            "Portfolio chat session not found or expired. "
            "Start a new conversation (sessions last 30 minutes)."
        )