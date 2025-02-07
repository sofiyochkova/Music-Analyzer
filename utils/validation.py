def request_method_is_post(request_method: str):
    return request_method == "POST"

def is_not_empty(value: str) -> bool:
    return value is not None and value != ""

def is_time_period_valid(time_period: str):
    return time_period in ["7day", "1month", "3month", "6month", "12month", "overall", "custom"]

def are_dates_valid(start_date: str, end_date: str):
    pass


def is_file_extension_json(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == "json"
