from __future__ import print_function
import sys
import pickle
import io
import os.path
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

SCOPES = [
    'https://www.googleapis.com/auth/drive'
]

def authenticate(client_secret_json_path):
    """QuickStartで行った認証処理と同じ認証処理を行う
    https://developers.google.com/drive/api/v3/quickstart/python
    """
    creds = None
    # ファイルtoken.pickleはユーザーのアクセストークンと更新トークンを格納し、
    # 認証フローが初めて完了すると自動的に作成されます。
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # 有効な資格情報がない場合は、ユーザーにログインさせます。
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # ユーザーにブラウザーで認証URLを開くように指示し、ユーザーのURLを自動的に開こうとします。
            # ローカルWebサーバーを起動して、認証応答をリッスンします。
            # 認証が完了すると、認証サーバーはユーザーのブラウザーをローカルWebサーバーにリダイレクトします。
            # Webサーバーは、応答とシャットダウンから認証コードを取得します。その後、コードはトークンと交換されます
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_json_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # 次回実行のために「google.oauth2.credentials.Credentials」をシリアライズ化して保存します。
        # https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.credentials.html
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def wait_loading_cnt(service_sheets, file_id, name):
    result = service_sheets.spreadsheets().values().get(
        spreadsheetId=file_id,
        range="{}!B1:B".format(name)
    ).execute()
    load_cnt = 0
    for row in result.get('values'):
        if row[0] == 'Loading...' or row[0] == '読み込んでいます...':
            load_cnt += 1
    return load_cnt


def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 3:
        print("Usage #python %s [CSVのパス] [認証用JSONのパス]" % argvs[0])
        exit()
    csv_path = argvs[1]
    client_secret_json_path = argvs[2]

    creds = authenticate(client_secret_json_path)
    name = os.path.splitext(os.path.basename(csv_path))[0]

    service_drive = build('drive', 'v3', credentials=creds)

    # CSVをGoogleスプレッドシートで編集できるようにUploadします.
    # https://developers.google.com/drive/api/v3/manage-uploads#python
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    media = MediaFileUpload(csv_path,
                            mimetype='text/csv',
                            resumable=True)
    file = service_drive.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
    file_id = file.get('id')
    print('Upload File ID: %s' % file_id)

    # GoogleスプレッドシートのB列に翻訳用の数式を記述します。
    service_sheets = build('sheets', 'v4', credentials=creds)
    result = service_sheets.spreadsheets().values().get(
        spreadsheetId=file_id,
        range="{}!A1:A".format(name)
    ).execute()
    rec_cnt = len(result.get('values'))
    print("行数", rec_cnt)

    # 全ての行のB列とC列を書き換える
    requests = []
    requests.append({
        'repeatCellRequest' : {
            'properties' 
        }
    })
    values = []
    for i in range(len(result.get('values'))):
        values.append(
            [
                '=GOOGLETRANSLATE(indirect("RC[-1]", false),"en","ja")'
            ]
        )

    body = {
        'values': values
    }
    result = service_sheets.spreadsheets().values().update(
        spreadsheetId=file_id,
        range="{}!B1:B".format(name),
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))

    # loading...が亡くなるまで待つ
    loading_cnt = wait_loading_cnt(service_sheets, file_id, name)
    while loading_cnt != 0:
        loading_cnt = wait_loading_cnt(service_sheets, file_id, name)
        print('残り翻訳数 {0}/{1}'.format(loading_cnt, rec_cnt))
        time.sleep(10)

    # Download
    request = service_drive.files().export_media(fileId=file_id, mimeType='text/csv')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print ("Download %d%%." % int(status.progress() * 100))
    with open(csv_path, 'wb') as f:
        f.write(fh.getvalue())

if __name__ == '__main__':
    main(sys.argv)
