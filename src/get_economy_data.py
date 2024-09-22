import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

GOOGLE_SHEET_NAME = "Sim companies economy data"


def create(title: str):
  """
  Creates the Sheet the user has access to.
  Load pre-authorized user credentials from the environment.
  """
  creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"])
  try:
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = {"properties": {"title": title}}
    spreadsheet = (
        service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId")
        .execute()
    )
    print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get("spreadsheetId")
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


if __name__ == "__main__":
  create(GOOGLE_SHEET_NAME)