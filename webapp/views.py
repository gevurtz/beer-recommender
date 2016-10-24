from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/')
def start():
    return render_template('start.html')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/cover')
def cover():
    return render_template('cover.html')

@app.route('/results', methods=['POST'])
def url():
    return request.form['user_input']

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)