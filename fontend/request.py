import requests
import json

url = "http://127.0.0.1:5000/"


def send_diff_pic_request(pic_name,new_pic,old_pic):
    payload = json.dumps({
      "pic_name": pic_name,
      "new_pic": new_pic,
      "old_pic": old_pic

    })
    headers = {
      'Content-Type': 'application/json'
    }
    return requests.request("POST", url + "diffpicture", headers=headers, data=payload)


def send_load_project_request():
    payload = {}
    headers = {
      'Content-Type': 'application/json'
    }
    return requests.request("GET", url + "load_project", headers=headers, data=payload)

def send_load_history_pic_request(project,release):
    payload = {}
    headers = {
      'Content-Type': 'application/json'
    }
    return requests.request("GET", url + "load_history_pic?project={0}&release={1}".format(project, release), headers=headers, data=payload)

def save_pic_request(images,project,release):
    payload = json.dumps({
      "images": images,
      "project": project,
      "release": release
    })
    headers = {
      'Content-Type': 'application/json'
    }
    return requests.request("POST", url + "save_pic", headers=headers, data=payload)

