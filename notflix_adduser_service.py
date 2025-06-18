from flask import Flask, render_template, request, redirect
import logging
import requests
import sys
import json
import os
import bcrypt
from requests.exceptions import HTTPError

logging.basicConfig(filename='config/adduser.log',level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger().addHandler(logging.StreamHandler())
logging.debug('resrst')
# open the config file as read-only
try:
    config_file = open('/config/config.txt', 'r')
except:
    if os.environ['CONFIG'] :
        config_file = open(os.environ['CONFIG'], 'r')
    else:
        print('cannot find config file /config/config.txt')
        sys.exit()

config_settings = config_file.readlines()
config_file.close()

jellyfin_base_url = config_settings[0][18:].rstrip()
invite_code = config_settings[1][12:].rstrip()
filebrowser_api = config_settings[2][16:].rstrip()
filebrowser_adduser_url = config_settings[3][24:].rstrip()
jfadmin_adduser_url = config_settings[4][20:].rstrip()
npm_api_url = config_settings[7][12:].rstrip()
npm_user = config_settings[8][9:].rstrip()
npm_password = config_settings[9][13:].rstrip()
error_url = config_settings[5][10:].rstrip()
onboarding_url = config_settings[6][15:].rstrip()
api_obf='*' * len(filebrowser_api)
success_codes = ['200','201','301','302']
error_code = ['401','501']

print('Jellyfin Base URL : '+jellyfin_base_url)
print('Invite Code : '+invite_code)
print('Filebrowser API Key :'+api_obf)
print('Filebrowsr API URL Add User :'+filebrowser_adduser_url)
print('Jellyfin Admin API URL Add User :'+jfadmin_adduser_url)
print('NPM API BAse :'+npm_api_url)
print('Error Redirect :'+error_url)
print('Success Redirect :'+onboarding_url)

app = Flask(__name__)

@app.route('/adduser', methods=['POST'])
def adduser():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        code = request.form.get('code')

        admin_account = add_jfadmin(username,password,email,code)
        if admin_account == '200':
            fb_account = add_fb(username,password)
            if fb_account == '201':
                youtube_account = add_npm(username,password)
                if youtube_account == '200':
                    return redirect(onboarding_url, code=302)
                else:
                    return redirect(error_url+'?code='+youtube_account+'&msg=error', code=302)
            else:
                return redirect(error_url+'?code='+fb_account+'&msg=error', code=302)
        else:
            return redirect(error_url+'?code='+admin_account+'&msg=error', code=302)

        ## Filebrowser User Add

    else:
        return render_template('add_user.html')



def add_jfadmin(username: str, password: str, email: str, code: str):
    url = jfadmin_adduser_url;
    post_data = '{"code": "'+code+'", "email": "'+email+'", "username": "'+username+'", "password": "'+password+'"}'

    try:
        response = requests.post(url, data=post_data)
    except HTTPError as e:
        print(e.response.text)

    result = str(response.status_code)
    return result

def add_fb(username: str, password: str):
    url = filebrowser_adduser_url
    post_data='{"what":"user","which":[],"data":{"stickySidebar":true,"darkMode":true,"locale":"en","viewMode":"normal","singleClick":false,"showHidden":false,"dateFormat":false,"gallerySize":3,"themeColor":"var(--blue)","quickDownload":false,"disableOnlyOfficeExt":".txt .csv .html .pdf","disableOfficePreviewExt":"","lockPassword":false,"preview":{"highQuality":true,"image":true,"video":true,"motionVideoPreview":false,"office":false,"popup":true},"permissions":{"api":false,"admin":false,"modify":false,"share":true,"realtime":false},"loginMethod":"password","password":"'+password+'","scopes":[{"path":"/srv","name":"srv","config":{"indexingInterval":0,"disabled":false,"maxWatchers":0,"neverWatchPaths":null,"ignoreHidden":false,"ignoreZeroSizeFolders":false,"exclude":{"files":null,"folders":null,"fileEndsWith":null},"include":{"files":null,"folders":null,"fileEndsWith":null},"defaultUserScope":"/","defaultEnabled":true,"createUserDir":false}}],"username":"'+username+'"}}'
    header_api_key = 'Bearer '+filebrowser_api
    headers = { 'Authorization' : header_api_key, 'Accept' : 'application/json'}

    try:
        response = requests.post(url, data=post_data, headers=headers)
    except HTTPError as e:
        print(e.response.text)

    result = str(response.status_code)

    return result

def add_npm(username:str, password:str):
    api_url = npm_api_url #
    data = { 'identity': npm_user, 'secret': npm_password }
    npm_api = requests.post(api_url+'/tokens', data=data)
    print(npm_api.json()['token'])
    token = npm_api.json()['token'] 
    access_list_url = f"{api_url}/nginx/access-lists/4?expand=items"
    updated_list_url = f"{api_url}/nginx/access-lists/4" 
    # Get the current access list


    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        access_list = requests.get(access_list_url, headers=headers)
    except HTTPError as e:
        result = 'error'
        print(e.response.text)
        return result
    items = access_list.json()['items']
    new_user = {
                "username": username,
                "password": password
            }
    new_items = [] 
    new_items.append(new_user)
    for each in items:
        item = {"username": each['username'], "password": ""}
        new_items.append(item) 
    
    updated_access_list = {
              "name": "Updated YTPTube Accesss",
            "satisfy_any": True,
            "items": new_items
            }

    updated_access_list = json.dumps(updated_access_list)

    print(" ")
    print(updated_access_list)
    print(" ")
    try:
        result = str(requests.put(updated_list_url, data=updated_access_list, headers=headers).status_code)
    except HTTPError as e:
        result = '500'
        print(e.response.text)
    return str(result)

@app.route('/')
def home():
    return render_template('create.html')

from flask import send_from_directory

@app.route('/create_files/<path:path>')
def send_report(path):
    # Using request args for path will expose you to directory traversal attacks
    return send_from_directory('create_files', path)


if __name__ == '__main__':
        app.run(host="0.0.0.0", port=3000, debug=True)
