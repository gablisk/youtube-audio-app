import os
import subprocess
import glob
import zipfile
from flask import Flask, request, render_template, send_from_directory

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    download_links = []
    zip_link = None

    if request.method == 'POST':
        urls_raw = request.form.get('urls', '').strip()
        urls = [line.strip() for line in urls_raw.splitlines() if line.strip()]
        print(f'受け取ったURLリスト → {urls}')

        if not urls:
            message = 'URLが空です。もう一度入力してください。'
            return render_template('index.html', message=message)

        try:
            os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

            # 既存ファイル削除
            for file in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*")):
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"削除失敗: {file} ({e})")

            # 音声DL
            for url in urls:
                command = [
                    'yt-dlp',
                    '-x',
                    '--audio-format', 'mp3',
                    '--print', 'after_move:filepath',
                    '-o', os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                    url
                ]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                downloaded_path = result.stdout.strip()
                filename = os.path.basename(downloaded_path)
                download_links.append(f'/download/{filename}')

            # ZIP作成
            zip_path = os.path.join(DOWNLOAD_FOLDER, 'all_downloads.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.mp3")):
                    zipf.write(file, os.path.basename(file))
            zip_link = '/download/all_downloads.zip'

            message = f'{len(download_links)}件の音声ダウンロードが完了しました！'

        except subprocess.CalledProcessError as e:
            message = f'yt-dlpエラー: {e.stderr or str(e)}'
        except Exception as e:
            message = f'その他のエラー: {e}'

    return render_template('index.html', message=message, download_links=download_links, zip_link=zip_link)

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # RenderはこのPORT環境変数を自動で渡す
    app.run(host='0.0.0.0', port=port, debug=True)