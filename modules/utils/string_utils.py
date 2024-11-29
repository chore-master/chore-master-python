import shortuuid


class StringUtils:
    @staticmethod
    def new_short_id(length: int) -> str:
        return shortuuid.ShortUUID().random(length=length)
