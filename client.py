import requests,os 

BASE_URL = "http://127.0.0.1:8000"


def register(email: str, password: str, full_name: str = None, roles: str = None):
    payload = {"email": email, "password": password}
    if full_name:
        payload["full_name"] = full_name
    if roles:
        payload["roles"] = ["admin"]
    resp = requests.post(f"{BASE_URL}/register", json=payload)
    print(resp.json())
    return resp.json()


def login(username: str, password: str):
    data = {"username": username, "password": password}
    resp = requests.post(f"{BASE_URL}/token", data=data)
    resp.raise_for_status()
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
    #user = register("alice@example.com", "secret123", full_name="Alice", roles="admin")
    #print("Registered:", user)

    token = login("alice@example.com", "secret123")
    print("Token:", token)

    profile = get_profile(token)
    print("Profile:", profile)

    # If the user has admin role:
    try:
        admins = list_users(token)
        print("All users:", admins)
    except requests.HTTPError as e:
        print("Not authorized to list users:", e)
