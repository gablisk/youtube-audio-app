from flask import Flask, request, render_template, send_from_directory
import os
import subprocess
import glob
import zipfile

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    download_links = []
    zip_link = None

    if request.method == 'POST':
        url_input = request.form.get('url', '').strip()
        url_list = [url.strip() for url in url_input.splitlines() if url.strip()]
        print(f'受け取ったURLリスト → {url_list}')

        try:
            for url in url_list:
                command = [
                    'yt-dlp',
                    '-x',
                    '--audio-format', 'mp3',
                    '-o', os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                    url
                ]
                subprocess.run(command, check=True)

            # 直近のMP3ファイル一覧を取得
            mp3_files = sorted(glob.glob(os.path.join(DOWNLOAD_FOLDER, '*.mp3')), key=os.path.getmtime, reverse=True)
            for file in mp3_files[:len(url_list)]:
                download_links.append({'name': os.path.basename(file), 'link': f'/download/{os.path.basename(file)}'})

            # ZIPにまとめる
            zip_path = os.path.join(DOWNLOAD_FOLDER, 'all_downloads.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in download_links:
                    zipf.write(os.path.join(DOWNLOAD_FOLDER, file['name']), arcname=file['name'])

            zip_link = '/download/all_downloads.zip'
            message = '音声のダウンロードが完了しました！'

        except subprocess.CalledProcessError as e:
            message = f'yt-dlpエラー: {e.stderr or str(e)}'
        except Exception as e:
            message = f'その他のエラー: {e}'

    return render_template('index.html', message=message, download_links=download_links, zip_link=zip_link)

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # ← ここが Render で必要
    app.run(host='0.0.0.0', port=port)