def check_not_empty(value: str) -> bool:
    return value is not None and value != ""

def check_time_period(time_period: str):
    return time_period in ["7day", "1month", "3month", "6month", "12month", "overall", "custom"]


def check_dates(start_date: str, end_date: str):
    pass



