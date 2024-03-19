
# Link URL curl --request GET --url 'https://status.earthdata.nasa.gov/api/v1/notifications?client=LP%20DAAC%20Website%20(OPS)&alll=true'

import requests
from bs4 import BeautifulSoup

product_provider_lookup = {}

def get_service_status(product):
    """
    Prints to the console the service status of the Data Repository Provider through NASA's Status REST API
    """

    link = 'https://status.earthdata.nasa.gov/api/v1/notifications?client=LP%20DAAC%20Website%20(OPS)&alll=true'

    # Change provider if downloading GEDI04A
    if product in ["GEDI04_A"]:
        link = 'https://status.earthdata.nasa.gov/api/v1/notifications?client=ORNL%20DAAC%20Website%20(OPS)&alll=true'

    notifications_list = requests.get(link).json()['notifications']

    if len(notifications_list) > 0:
        for notif in notifications_list:
            id_num = notif['id']
            message = BeautifulSoup(notif['message'], features="html.parser").get_text()
            print(f"[Service Status] Message ID:{id_num} - {message}")
        return notifications_list
    else:
        print("[Service Status] No notifications available.")
        return notifications_list


if __name__ == '__main__':
    # TEST
    get_service_status("GEDI02_A")