
To create an virtual environment
python -m venv .venv
python3.12 -m venv .venv

To Activate the virtual environment
source .venv/bin/activate
export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"

To install dependency
pip install -r requirements.txt

To run the code
uvicorn app.main:app --reload

pip freeze > requirements.txt