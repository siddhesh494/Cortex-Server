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