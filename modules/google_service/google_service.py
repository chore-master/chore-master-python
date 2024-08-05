from contextlib import contextmanager
from typing import Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from modules.google_service.models.logical_sheet import LogicalColumn, LogicalSheet


class GoogleService:
    spreadsheet_mime_type = "application/vnd.google-apps.spreadsheet"

    @staticmethod
    def sheet_column_name(column_index: int) -> str:
        result = ""
        column_index += 1
        while column_index > 0:
            column_index, remainder = divmod(column_index - 1, 26)
            result = f"{chr(65 + remainder)}{result}"
        return result

    def __init__(self, credentials: Credentials):
        self._credentials = credentials
        # https://developers.google.com/drive/api/guides/about-files
        self._drive_service: Resource = build(
            serviceName="drive", version="v3", credentials=credentials
        )
        # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets
        self._sheets_service: Resource = build(
            serviceName="sheets", version="v4", credentials=credentials
        )

    @contextmanager
    def batch_update_spreadsheet_session(self, spreadsheet_id: str):
        batch_update_requests = []
        yield batch_update_requests
        if len(batch_update_requests) > 0:
            result = (
                self._sheets_service.spreadsheets()
                .batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": batch_update_requests},
                )
                .execute()
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

    def get_spreadsheet(self, spreadsheet_id: str) -> dict:
        spreadsheet = (
            self._sheets_service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id)
            .execute()
        )
        return spreadsheet

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

    def reflect_logical_sheet(
        self, spreadsheet_id: str, sheet_title: str, should_include_body: bool = False
    ) -> Tuple[Optional[LogicalSheet], Optional[dict], Optional[list]]:
        spreadsheet = (
            self._sheets_service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id)
            .execute()
        )
        sheet_dicts = spreadsheet.get("sheets", [])
        sheet_dict = next(
            (s for s in sheet_dicts if s["properties"]["title"] == sheet_title),
            None,
        )
        if sheet_dict is None:
            return None, None, None

        grid_dict = sheet_dict["properties"]["gridProperties"]
        reflected_column_count = grid_dict["columnCount"]
        reflected_row_count = grid_dict["rowCount"]
        logical_sheet = LogicalSheet(logical_name=sheet_title, logical_columns=[])
        # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchGet
        left_column_name = self.sheet_column_name(
            logical_sheet.preserved_raw_column_count
        )
        right_column_name = self.sheet_column_name(reflected_column_count - 1)
        ranges = []
        header_range = f"{sheet_title}!{left_column_name}1:{right_column_name}{logical_sheet.preserved_raw_row_count}"
        ranges.append(header_range)
        if (
            should_include_body
            and logical_sheet.preserved_raw_row_count < reflected_row_count
        ):
            body_range = f"{sheet_title}!{left_column_name}{logical_sheet.preserved_raw_row_count + 1}:{right_column_name}{reflected_row_count}"
            ranges.append(body_range)
        result = (
            self._sheets_service.spreadsheets()
            .values()
            .batchGet(
                spreadsheetId=spreadsheet_id,
                majorDimension="COLUMNS",
                valueRenderOption="FORMATTED_VALUE",
                dateTimeRenderOption="SERIAL_NUMBER",
                ranges=ranges,
            )
            .execute()
        )
        value_ranges = result.get("valueRanges", [])
        reflected_header_values = value_ranges[0].get("values", [])
        if len(value_ranges) > 1:
            reflected_body_values = value_ranges[1].get("values", [])
        else:
            reflected_body_values = []

        for reflected_raw_column_offset, reflected_column_series in enumerate(
            reflected_header_values
        ):
            reflected_column_series_generator = iter(reflected_column_series)
            logical_column_name = next(reflected_column_series_generator, None)
            if logical_column_name is None:
                continue
            logical_data_type_name = next(reflected_column_series_generator, None)
            logical_is_nullable = next(reflected_column_series_generator, None)
            logical_is_primary_key = next(reflected_column_series_generator, None)
            logical_is_unique_key = next(reflected_column_series_generator, None)
            logical_column = LogicalColumn(
                logical_name=logical_column_name,
                logical_data_type_name=logical_data_type_name,
                logical_is_nullable=logical_is_nullable,
                logical_is_primary_key=logical_is_primary_key,
                logical_is_unique_key=logical_is_unique_key,
                raw_index=logical_sheet.preserved_raw_column_count
                + reflected_raw_column_offset,
            )
            logical_sheet.logical_columns.append(logical_column)
        return (
            logical_sheet,
            sheet_dict,
            reflected_body_values[: len(logical_sheet.logical_columns)],
        )

    def create_logical_sheet(self, spreadsheet_id: str, logical_sheet: LogicalSheet):
        batch_update_requests = [
            {
                "addSheet": {
                    "properties": {
                        "title": logical_sheet.logical_name,
                        "gridProperties": {
                            "rowCount": logical_sheet.preserved_raw_row_count,
                            "columnCount": logical_sheet.preserved_raw_column_count,
                        },
                    }
                }
            }
        ]
        result = (
            self._sheets_service.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": batch_update_requests},
            )
            .execute()
        )
        sheet_dict = result["replies"][0]["addSheet"]
        return sheet_dict

    def migrate_logical_sheet(self, spreadsheet_id: str, logical_sheet: LogicalSheet):
        reflected_logical_sheet, reflected_sheet_dict, _ = self.reflect_logical_sheet(
            spreadsheet_id=spreadsheet_id, sheet_title=logical_sheet.logical_name
        )
        if reflected_logical_sheet is None or reflected_sheet_dict is None:
            self.create_logical_sheet(
                spreadsheet_id=spreadsheet_id,
                logical_sheet=LogicalSheet(
                    logical_name=logical_sheet.logical_name,
                    logical_columns=[],
                ),
            )
            reflected_logical_sheet, reflected_sheet_dict, _ = (
                self.reflect_logical_sheet(
                    spreadsheet_id=spreadsheet_id,
                    sheet_title=logical_sheet.logical_name,
                    should_include_body=False,
                )
            )

        sheet_id = reflected_sheet_dict["properties"]["sheetId"]

        column_name_to_reflected_logical_sheet_column_map = (
            reflected_logical_sheet.logical_column_name_to_logical_column_map
        )
        reflected_logical_sheet_column_names_set = set(
            c.logical_name for c in reflected_logical_sheet.logical_columns
        )

        column_name_to_logical_sheet_column_map = (
            logical_sheet.logical_column_name_to_logical_column_map
        )
        logical_sheet_column_names_set = set(
            c.logical_name for c in logical_sheet.logical_columns
        )

        updatable_logical_sheet_column_names_set = (
            reflected_logical_sheet_column_names_set & logical_sheet_column_names_set
        )
        removable_logical_sheet_column_names_set = (
            reflected_logical_sheet_column_names_set - logical_sheet_column_names_set
        )
        insertable_logical_sheet_column_names_set = (
            logical_sheet_column_names_set - reflected_logical_sheet_column_names_set
        )

        with self.batch_update_spreadsheet_session(
            spreadsheet_id
        ) as batch_update_requests:
            # ensure preserved columns
            reflected_raw_sheet_column_count = reflected_sheet_dict["properties"][
                "gridProperties"
            ]["columnCount"]
            if (
                reflected_raw_sheet_column_count
                < logical_sheet.preserved_raw_column_count
            ):
                batch_update_requests.append(
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": reflected_raw_sheet_column_count,
                                "endIndex": logical_sheet.preserved_raw_column_count,
                            },
                            "inheritFromBefore": True,
                        }
                    }
                )

            # ensure preserved rows
            reflected_raw_sheet_row_count = reflected_sheet_dict["properties"][
                "gridProperties"
            ]["rowCount"]
            if reflected_raw_sheet_row_count < logical_sheet.preserved_raw_row_count:
                batch_update_requests.append(
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": reflected_raw_sheet_row_count,
                                "endIndex": logical_sheet.preserved_raw_row_count,
                            },
                            "inheritFromBefore": True,
                        }
                    }
                )

            # update logical columns
            for logical_column_name in updatable_logical_sheet_column_names_set:
                reflected_logical_sheet_column = (
                    column_name_to_reflected_logical_sheet_column_map[
                        logical_column_name
                    ]
                )
                logical_sheet_column = column_name_to_logical_sheet_column_map[
                    logical_column_name
                ]
                batch_update_requests.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": logical_sheet.preserved_raw_row_count,
                                "startColumnIndex": reflected_logical_sheet_column.raw_index,
                                "endColumnIndex": reflected_logical_sheet_column.raw_index
                                + 1,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": logical_sheet_column.logical_name
                                            }
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": logical_sheet_column.logical_data_type_name
                                            }
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": f"{logical_sheet_column.logical_is_nullable}"
                                            }
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": f"{logical_sheet_column.logical_is_primary_key}"
                                            }
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": f"{logical_sheet_column.logical_is_unique_key}"
                                            }
                                        }
                                    ]
                                },
                            ],
                            "fields": "userEnteredValue",
                        }
                    }
                )

            # remove logical columns from right to left (to prevent index shift)
            removed_raw_column_count = len(removable_logical_sheet_column_names_set)
            sorted_removable_logical_sheet_column_names = sorted(
                removable_logical_sheet_column_names_set,
                key=lambda c: column_name_to_reflected_logical_sheet_column_map[
                    c
                ].raw_index,
                reverse=True,
            )

            for logical_column_name in sorted_removable_logical_sheet_column_names:
                reflected_logical_sheet_column = (
                    column_name_to_reflected_logical_sheet_column_map[
                        logical_column_name
                    ]
                )
                batch_update_requests.append(
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": reflected_logical_sheet_column.raw_index,
                                "endIndex": reflected_logical_sheet_column.raw_index
                                + 1,
                            }
                        }
                    }
                )

            # insert logical columns
            insertable_logical_sheet_columns_count = len(
                insertable_logical_sheet_column_names_set
            )
            if insertable_logical_sheet_columns_count > 0:
                insert_raw_column_index = (
                    logical_sheet.preserved_raw_column_count
                    + len(reflected_logical_sheet.logical_columns)
                    - removed_raw_column_count
                )
                batch_update_requests.append(
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": insert_raw_column_index,
                                "endIndex": insert_raw_column_index
                                + insertable_logical_sheet_columns_count,
                            },
                            "inheritFromBefore": insert_raw_column_index > 0,
                        }
                    }
                )
                for column_index_offset, logical_column_name in enumerate(
                    insertable_logical_sheet_column_names_set
                ):
                    logical_sheet_column = column_name_to_logical_sheet_column_map[
                        logical_column_name
                    ]
                    batch_update_requests.append(
                        {
                            "updateCells": {
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": 0,
                                    "endRowIndex": logical_sheet.preserved_raw_row_count,
                                    "startColumnIndex": insert_raw_column_index
                                    + column_index_offset,
                                    "endColumnIndex": insert_raw_column_index
                                    + column_index_offset
                                    + 1,
                                },
                                "rows": [
                                    {
                                        "values": [
                                            {
                                                "userEnteredValue": {
                                                    "stringValue": logical_sheet_column.logical_name
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "values": [
                                            {
                                                "userEnteredValue": {
                                                    "stringValue": logical_sheet_column.logical_data_type_name
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "values": [
                                            {
                                                "userEnteredValue": {
                                                    "stringValue": f"{logical_sheet_column.logical_is_nullable}"
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "values": [
                                            {
                                                "userEnteredValue": {
                                                    "stringValue": f"{logical_sheet_column.logical_is_primary_key}"
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "values": [
                                            {
                                                "userEnteredValue": {
                                                    "stringValue": f"{logical_sheet_column.logical_is_unique_key}"
                                                }
                                            }
                                        ]
                                    },
                                ],
                                "fields": "userEnteredValue",
                            }
                        }
                    )
