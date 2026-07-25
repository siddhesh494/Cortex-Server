from fastapi.responses import JSONResponse


class ApiResponse:

    @staticmethod
    def success(
        data=None,
        message: str = "Success",
        status_code: int = 200
    ):
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "message": message,
                "data": data
            }
        )

    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        data=None
    ):
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "data": data
            }
        )