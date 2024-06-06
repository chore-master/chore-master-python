from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build


class GoogleService:
    spreadsheet_mime_type = "application/vnd.google-apps.spreadsheet"

    def __init__(self, credentials: Credentials):
        self._credentials = credentials
        # https://developers.google.com/drive/api/guides/about-files
        self._drive_service: Resource = build(
            serviceName="drive", version="v3", credentials=credentials
        )
        # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets
        self._sheet_service: Resource = build(
            serviceName="sheets", version="v4", credentials=credentials
        )

    def find_spreadsheet_file_or_none(
        self, parent_folder_id: str, spreadsheet_name: str
    ) -> Optional[dict]:
        result = (
            self._drive_service.files()
            .list(
                q=(
                    f"'{parent_folder_id}' in parents and "
                    f"name = '{spreadsheet_name}' and "
                    f"mimeType='{self.spreadsheet_mime_type}' and"
                    "trashed=false"
                ),
                fields="files(id, name)",
            )
            .execute()
        )
        files = result.get("files", [])
        return next((f for f in files), None)

    def create_spreadsheet_file(self, parent_folder_id: str, file_name: str) -> dict:
        file_metadata = {
            "name": file_name,
            "mimeType": self.spreadsheet_mime_type,
            "parents": [parent_folder_id],
        }
        file = (
            self._drive_service.files()
            .create(body=file_metadata, fields="id, name")
            .execute()
        )
        return file

    def migrate_spreadsheet_file(
        self, parent_folder_id: str, spreadsheet_name: str
    ) -> dict:
        spreadsheet_file_dict = self.find_spreadsheet_file_or_none(
            parent_folder_id, spreadsheet_name
        )
        if spreadsheet_file_dict is None:
            spreadsheet_file_dict = self.create_spreadsheet_file(
                parent_folder_id, spreadsheet_name
            )
        return spreadsheet_file_dict

    def migrate_sheet(self):
        pass

    def _migrate_sheet(self):
        spreadsheet = (
            self._sheets_service.spreadsheets()
            .get(spreadsheetId=self._spreadsheet_id)
            .execute()
        )
        sheets = spreadsheet.get("sheets", [])
        sheet = next(
            (s for s in sheets if s["properties"]["title"] == self.sheet.title),
            None,
        )
        if sheet is None:
            # create sheet
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self._spreadsheet_id,
                    body={
                        "requests": [
                            {
                                "addSheet": {
                                    "properties": {
                                        "title": self.sheet.title,
                                        "gridProperties": {
                                            "rowCount": len(
                                                self.preserved_row_names._fields
                                            ),
                                            "columnCount": len(
                                                self.preserved_row_names._fields
                                            ),
                                        },
                                    }
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
            sheet = result["replies"][0]["addSheet"]

        # new_dimensions = []
        # update_dimensions = []
        # deprecate_dimensions = []

        sheet_id = sheet["properties"]["sheetId"]
        reflected_column_count = sheet["properties"]["gridProperties"]["columnCount"]
        batch_udpate_requests = []
        delete_column_count = 0

        # reflect sheet
        result = (
            self._sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=self._spreadsheet_id,
                majorDimension="COLUMNS",
                range=f"{self.sheet_title}!A1:{self.column_name(reflected_column_count)}{len(self.preserved_row_names._fields)}",
            )
            .execute()
        )
        field_names_set = set(self.entity_class.model_fields.keys())
        reflected_field_names_set = set()
        reflected_values = result.get("values", [])

        # iterate over existing columns to detect differences
        field_types = typing.get_type_hints(self.entity_class)
        for column_index in range(reflected_column_count):
            # delete redundant columns
            if column_index >= len(reflected_values):
                batch_udpate_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index - delete_column_count,
                                "endIndex": column_index - delete_column_count + 1,
                            }
                        }
                    }
                )
                delete_column_count += 1
                continue

            # delete redundant columns
            series = reflected_values[column_index]
            if len(series) != len(self.preserved_row_names._fields):
                batch_udpate_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index - delete_column_count,
                                "endIndex": column_index - delete_column_count + 1,
                            }
                        }
                    }
                )
                delete_column_count += 1
                continue

            # delete deprecated columns
            reflected_field_name, reflected_field_type_name = series
            reflected_field_names_set.add(reflected_field_name)
            if reflected_field_name not in self.entity_class.model_fields:
                batch_udpate_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index - delete_column_count,
                                "endIndex": column_index - delete_column_count + 1,
                            }
                        }
                    }
                )
                delete_column_count += 1
                continue

            # update columns
            field_info = self.entity_class.model_fields[reflected_field_name]
            field_type_name = field_info.annotation.__name__
            if reflected_field_type_name != field_type_name:
                batch_udpate_requests.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 1,
                                "startColumnIndex": len(
                                    self.preserved_column_names._fields
                                )
                                + column_index,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": field_type_name
                                            }
                                        }
                                    ]
                                },
                            ],
                            "fields": "userEnteredValue",
                        }
                    }
                )

        # create columns
        new_field_names_set = field_names_set.difference(reflected_field_names_set)
        insert_column_start_index = (
            len(self.preserved_column_names._fields)
            + reflected_column_count
            - delete_column_count
        )
        new_columns_count = len(new_field_names_set)
        if new_columns_count > 0:
            batch_udpate_requests.append(
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": insert_column_start_index,
                            "endIndex": insert_column_start_index + new_columns_count,
                        },
                        "inheritFromBefore": insert_column_start_index > 0,
                    }
                }
            )

            for i, field_name in enumerate(new_field_names_set):
                field_info = self.entity_class.model_fields[field_name]
                batch_udpate_requests.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "startColumnIndex": insert_column_start_index + i,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": field_name
                                            }
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": field_info.annotation.__name__
                                            }
                                        }
                                    ]
                                },
                            ],
                            "fields": "userEnteredValue",
                        }
                    }
                )

        if len(batch_udpate_requests) > 0:
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=self._spreadsheet_id,
                    body={"requests": batch_udpate_requests},
                )
                .execute()
            )
            print("Migration done", batch_udpate_requests, result)
        else:
            print("Migration done: no difference")
