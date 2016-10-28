import graphlab as gl

def load_gl_model(name):
    return gl.load_model(name)

def input_to_sframe(beer_rating_pairs):
    unzipped = [list(x) for x in zip(*beer_rating_pairs)]
    new_data = gl.SFrame()
    new_data['beerid'], new_data['overall'] = unzipped[1], unzipped[0]
    return new_data

def get_recommendation(new_data, model):
    model = load_gl_model(model)
    sf_new = input_to_sframe(new_data)
    recs = model.recommend_from_interactions(sf_new)
    return str(list(recs))