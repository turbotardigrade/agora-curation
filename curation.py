from sklearn.feature_extraction.text import HashingVectorizer
from sklearn import preprocessing
from sklearn.naive_bayes import MultinomialNB
from sklearn.externals import joblib
from scipy import sparse
import sqlite3

conn = sqlite3.connect("database.db")
clf = joblib.load("model.pkl")
word_vectorizer = HashingVectorizer(decode_error='ignore',
                                    n_features=2 ** 10, non_negative=True)
bigram_vectorizer = HashingVectorizer(analyzer='char', n_features=2 ** 10,
                                      non_negative=True, ngram_range=(1,2))
""" transform_data accepts a data array and transforms it into
    the model vector format """
def transform_data(data):
    """ The data format of the trained schema is:
        data[0] transformed by bigram_vectorizer (1024 features)
        data[0] transformed by word_vectorizer (1024 features)
        data[1] transformed by word_vectorizer (1024 features)
        data[2] transformed by word_vectorizer (1024 features) """


""" OnPostAdded will be called when new posts are retrieved
    from other peers, if this functions returns false, the
    content will be rejected (e.g. in the case of spam) and not
    stored by our node """
def on_post_added(args):
    if args["isWhitelabeled"] == True:
        return {"result": True, "error": None}
    args['obj']


""" OnCommentAdded will be called when new comments are
    retrieved from other peers, if this functions returns
    false, the content will be rejected (e.g. in the case of
    spam) and not stored by our node """
def on_comment_added(args):
    if args["isWhitelabeled"] == True:
        return {"result": True, "error": None}
    args['obj']

""" GetContent gives back an ordered array of post hashes of
    suggested content by the curation module """
def get_content(args):
    # TODO: Use lerot to implement this function...?
    sql = """SELECT hash
             FROM posts
             ORDER BY flag"""
    args['params']

""" FlagContent marks or unmarks hashes as spam. True means
    content is flagged as spam, false means content is not
    flagged as spam """
def flag_content(args):
    # TODO: train using this example
    args['hash']
    args['isFlagged']

""" UpvoteContent is called when user upvotes content """
def upvote_content(args):
    # TODO: train using this example
    args['hash']

""" DownvoteContent is called when user downvotes content """
def downvote_content(args):
    # TODO: train using this example
    args['hash']
