import graphlab as gl
import cPickle as pickle
import pandas as pd

def load_gl_model(name):
    return gl.load_model(name)

def input_to_sframe(beer_rating_pairs):
    unzipped = [list(x) for x in zip(*beer_rating_pairs)]
    new_data = gl.SFrame()
    new_data['beerid'], new_data['overall'] = unzipped[1], unzipped[0]
    return new_data

def get_new_recommendation(new_data, model):
    model = load_gl_model(model)
    sf_new = input_to_sframe(new_data)
    recs = model.recommend_from_interactions(sf_new)
    return list(recs)

def established_user_rec(user, model):
    model = load_gl_model(model)
    recs = model.recommend([user])
    return list(recs)

def load_users():
    with open('objs/users.pkl', 'r') as f:
        users = pickle.load(f)
    return users

def is_user(user):
    users = load_users()
    return user in users

def load_beers():
    with open('objs/beer_list.pkl', 'r') as f:
        beer_list = pickle.load(f)
    return beer_list

def format_results(recs):
    df_recs = pd.DataFrame(recs)
    beers = load_beers()
    table = df_recs.merge(beers, 'left')
    table.drop(['beerid', 'userid'], axis=1, inplace=True)
    table = table.round(2)
    table.columns = ['Rank', 'Predicted Score', 'Name', 'Brewery', 'Style']
    html_table = table.to_html(index=False, classes='table')
    return html_table

    