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
npm_api = config_settings[8][8:].rstrip()
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
print('NPM API Key :'+npm_api)
print('Error Redirect :'+error_url)
print('Success Redirect :'+onboarding_url)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def webroot():
    return 'ok 200'

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
            result = admin_account+fb_account
        else:
            result = admin_account+'500' 
#        print(fb_account)
        match result:
            case '200201': return redirect(onboarding_url, code=302)
            case '200500': return redirect(error_url+'?code='+result+'&msg=error', code=302)
            case '401201': return redirect(error_url+'?code='+result+'&msg=error', code=302)
            case _: return redirect(error_url+'?code='+result+'&msg=error', code=302)

        #    case '401500': print('ok')
        #    case '401': return redirect(error_url+'?code='+response_result+'&msg=duplicate account&refer=accounts.pknw1.co.uk', code=302)
        #    case _: return redirect(error_url+'?code='+response_result+'&msg=unknownerror&refer=accounts.pknw1.co.uk', code=302)

        ## Filebrowser User Add

    else:
        return render_template('add_user.html')

    return result


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
    api_url = npm_api_url #'https://proxymanager.admin.pknw1.co.uk/api'
    token = npm_api 
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
    
    access_list_json = access_list.json()
    items = access_list_json.get("items", [])
    new_id = max(item["id"] for item in items) + 1 if items else 1
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    items.append({"username": username, "password": password_hash,"id":new_id})
    access_list_json['items'] = items

    access_list_obj=json.dumps(access_list_json)

    try:
        updated_access_list = requests.put(updated_list_url, data=access_list_obj, headers=headers)
    except HTTPError as e:
        result = 'error'
        print(e.response.text)
        return result

    return updated_access_list.text


#result = update_access_list(api_base_url, api_token, new_username, new_password)

if __name__ == '__main__':
        app.run(host="0.0.0.0", port=3000, debug=True)
