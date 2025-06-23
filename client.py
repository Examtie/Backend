import requests,os 

BASE_URL = "https://examtieapi.breadtm.xyz"


def register(email: str, password: str, full_name: str = None, roles: str = None):
    payload = {"email": email, "password": password, "username": email.split("@")[0]}
    if full_name:
        payload["full_name"] = full_name
    if roles:
        payload["roles"] = ["admin"]
    resp = requests.post(f"{BASE_URL}/auth/api/v1/register", json=payload, verify=False)
    print(resp.json())
    return resp.json()


def login(username: str, password: str):
    data = {"username": username, "password": password}
    resp = requests.post(f"{BASE_URL}/token", data=data)
    return resp.json()["access_token"]


def get_profile(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(resp.text)
    #return resp.json()


def list_users(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # Example usage
    user = register("urmomomy@gomc.co", "dasdasdasd", full_name="Alicewang", roles="admin")
    user = register("dlllll@go.com", "dasdasdasd", full_name="Alicewang", roles="admin")
    # #print("Registered:", user)

    # token = login("aliceskibditoliet@gomc.co", "ddddddddd")
    # print("Token:", token)

    # profile = get_profile(token)
    # print("Profile:", profile)

    # # If the user has admin role:
    # try:
    #     admins = list_users(token)
    #     print("All users:", admins)
    # except requests.HTTPError as e:
    #     print("Not authorized to list users:", e)
