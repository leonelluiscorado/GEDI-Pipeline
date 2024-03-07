from datetime import datetime

def get_date_from_gedi_fn(granule_name):
    """
    Transforms Julian Date present in the GEDI Filenames by default into
    a date string with format YYYY/mm/dd (e.g. 2024/03/06)

    Args -
        granule_name: str
    Returns -
        date_sec (date_section) str in format YYYY/mm/dd
    """
    filename = granule_name.split("/")[-1]
    julian_date = filename.split("_")[2][0:7]
    date_sec = datetime.strptime(julian_date, "%Y%j").date()
    date_sec = date_sec.strftime("%Y/%m/%d")
    return date_sec