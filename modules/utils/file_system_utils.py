import glob
import os


class FileSystemUtils:
    @staticmethod
    def ensure_directory(directory_path: str):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

    @staticmethod
    def match_paths(pattern: str, recursive: bool = False) -> list[str]:
        return glob.glob(pattern, recursive=recursive)

    @staticmethod
    def match_one_path(pattern: str) -> str:
        paths = FileSystemUtils.match_paths(pattern)
        if len(paths) == 0:
            raise ValueError(f"No files found for `{pattern}`")
        if len(paths) > 1:
            raise ValueError(
                "\n".join([f"Multiple files found for `{pattern}`:", *paths])
            )
        return paths[0]
