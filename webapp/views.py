from sys import argv
from flask import Flask, request, render_template
import profile_scraper as ps
import loadmodel as mod
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
    profile = request.form['user_input']
    user_id = int(profile.split('/')[-2])
    reviews = ps.scrapeProfile(user_id)
    return mod.get_recommendation(reviews, 'rankmodel')


if __name__ == '__main__':
    if len(argv) > 1:
        if argv[1] == 'local':
            app.run(host='0.0.0.0', debug=True)
        elif argv[1] == 'open':
            app.run(host='0.0.0.0', port=80, debug=False)
        else: print 'invalid args: use args "local" to run on localhost w/ debug enabled or "open" to run on port 80, w/ debug disabled'

    else: print 'specify args "local" or "open"'