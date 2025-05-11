import os
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from zipfile import ZipFile
from PIL import Image
import shutil
from apkutils import APK

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'apk'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return '''
    <form method=post enctype=multipart/form-data action="/upload">
      <input type=file name=apk>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/upload', methods=['POST'])
def upload_apk():
    file = request.files['apk']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # APK解析
        apk = APK(filepath)
        manifest = apk.get_manifest()
        package_name = manifest['package']
        version_name = manifest['android:versionName']

        # アイコン抽出（例：最初に見つけたアイコンを保存）
        icon_data = apk.get_file(apk.get_icon())
        icon_path = os.path.join(app.config['OUTPUT_FOLDER'], 'icon.png')
        with open(icon_path, 'wb') as f:
            f.write(icon_data)

        # HTML作成
        html_path = os.path.join(app.config['OUTPUT_FOLDER'], 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(render_template('result.html',
                                    package=package_name,
                                    version=version_name))

        # ZIP圧縮
        zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{package_name}.zip')
        with ZipFile(zip_path, 'w') as zipf:
            zipf.write(html_path, arcname='index.html')
            zipf.write(icon_path, arcname='icon.png')

        return f'<a href="/download/{package_name}.zip">ダウンロードリンク</a>'

    return 'APKファイルをアップロードしてください'

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
