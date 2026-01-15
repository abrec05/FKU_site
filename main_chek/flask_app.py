from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import tempfile
import os
import logging

from src.parsers.config_parser import ConfigParser
from src.excel_processor import ExcelProcessor
from src.context_builder import ContextBuilder

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.route('/api/process', methods=['POST'])
def process():
    # Проверяем наличие первого файла
    if 'file1' not in request.files:
        return jsonify({'error': 'file1 is required'}), 400
    file1 = request.files['file1']
    # Второй файл необязателен; если не передан, используем дефолтный
    file2 = request.files.get('file2')

    # Создаём временную папку для сохранения загруженных файлов
    temp_dir = tempfile.mkdtemp(prefix='excel_proc_')
    path1 = os.path.join(temp_dir, file1.filename)
    file1.save(path1)

    if file2:
        path2 = os.path.join(temp_dir, file2.filename)
        file2.save(path2)
    else:
        # Путь к дефолтному тестовому файлу
        path2 = os.path.join('data', 'test_zak.xlsx')
        if not os.path.exists(path2):
            return jsonify({'error': f'Default file not found at {path2}'}), 500

    try:
        # Запуск той же логики, что и в GUI
        cfg = ConfigParser("config")
        proc = ExcelProcessor(cfg)
        builder = ContextBuilder(cfg, proc)
        df, report = builder.build(path1, path2)

        # Возвращаем отчёт в виде plain text
        response = make_response(report)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response
    except Exception as e:
        logging.exception("Ошибка при обработке файлов")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Слушаем на всех интерфейсах для доступа из LAN
    app.run(host='0.0.0.0', port=5000, debug=True)
