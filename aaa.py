# # # pip install requests
# # import requests
# # import time
 
# # # TODO: set your config
# # api_key = "CAP-D5903264575AE0571295C9D7A21B097F"  # your api key of capsolver
# # site_key = "6Lf6p74mAAAAAK5a7Fbo7UGiYacCmyI1ed8Tk2Q_"  # site key of your target site
# # site_url = "https://science.buu.ac.th/posn/pages/register_conf.php"  # page url of your target site
 
 
# # def capsolver():
# #     payload = {
# #         "clientKey": api_key,
# #         "task": {
# #             "type": 'ReCaptchaV2TaskProxyLess',
# #             "websiteKey": site_key,
# #             "websiteURL": site_url
# #         }
# #     }
# #     res = requests.post("https://api.capsolver.com/createTask", json=payload)
# #     resp = res.json()
# #     task_id = resp.get("taskId")
# #     if not task_id:
# #         print("Failed to create task:", res.text)
# #         return
# #     print(f"Got taskId: {task_id} / Getting result...")
 
# #     while True:
# #         #time.sleep(3)  # delay
# #         payload = {"clientKey": api_key, "taskId": task_id}
# #         res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
# #         resp = res.json()
# #         print(resp)
# #         status = resp.get("status")
# #         if status == "ready":
# #             return resp.get("solution", {}).get('gRecaptchaResponse')
# #         if status == "failed" or resp.get("errorId"):
# #             print("Solve failed! response:", res.text)
# #             return


# # cookies = {
# #     'PHPSESSID': '886b6fbf3f219603b0cc0e1406249904',
# # }

# # headers = {
# #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# #     'accept-language': 'en-US,en;q=0.9',
# #     'cache-control': 'max-age=0',
# #     'content-type': 'application/x-www-form-urlencoded',
# #     'origin': 'https://science.buu.ac.th',
# #     'priority': 'u=0, i',
# #     'referer': 'https://science.buu.ac.th/posn/pages/register_conf.php',
# #     'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
# #     'sec-ch-ua-mobile': '?0',
# #     'sec-ch-ua-platform': '"macOS"',
# #     'sec-fetch-dest': 'document',
# #     'sec-fetch-mode': 'navigate',
# #     'sec-fetch-site': 'same-origin',
# #     'sec-fetch-user': '?1',
# #     'upgrade-insecure-requests': '1',
# #     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
# #     # 'cookie': 'PHPSESSID=886b6fbf3f219603b0cc0e1406249904',
# # }

# # while True:
# #     token = capsolver()
# #     data = {
# #         'school': '170',
# #         'cid': '1250101727964',
# #         'pre': '1',
# #         'fname': 'พีรพัฒน์',
# #         'lname': 'กลิ่นนิ่ม',
# #         'birthday': '2009-01-28',
# #         'degree': '6',
# #         'nationality': '1',
# #         'address': 'ต.กรอกสมบูรณ์ จ.ปราจีนบุรี อ.ศรีมหาโพธิ 25140 126/12 หมู่ 3 ซอย 3',
# #         'zipcode': '25140',
# #         'tel': '0639407443',
# #         'email': 'std67443756@pra.ac.th',
# #         'password': 'Regenxy1234!',
# #         'g-recaptcha-response': token,
# #         'registConf': 'submit',
# #     }

# #     response = requests.post('https://science.buu.ac.th/posn/pages/register_process.php', cookies=cookies, headers=headers, data=data)
# #     print(response.text)
import requests


# cookies = {
#     'PHPSESSID': '886b6fbf3f219603b0cc0e1406249904',
# }

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://science.buu.ac.th',
    'priority': 'u=0, i',
    'referer': 'https://science.buu.ac.th/posn/pages/login.php',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    # 'cookie': 'PHPSESSID=886b6fbf3f219603b0cc0e1406249904',
}

while True:
    r = requests.get("https://science.buu.ac.th/posn/pages/verify_email.php?token=8U4Vct6Ezk60PKOPT5FqHU0Uz7rCGPZNZIgGpxELzuk6m9Dd9Fnu7DgyYoVw", headers=headers, timeout=None)
    print(r.text)
# data = {
#     'cid': '1250101727964',
#     'password': 'Regenxy1234!',
#     'submit': 'submit',
# }

# while True:
#     print(1)
#     response = requests.post('https://science.buu.ac.th/posn/pages/login.php', cookies=cookies, headers=headers, data=data, timeout=None)
#     print(response.headers)
#     print(response.text)