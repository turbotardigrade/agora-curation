from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.externals import joblib
from scipy import sparse
from datetime import timedelta
import numpy as np
import sqlite3
import warnings
import os, sys

with warnings.catch_warnings():
    warnings.simplefilter("ignore")

os.chdir(os.path.dirname(sys.executable))

comment = joblib.load("comment.pkl")
post = joblib.load("post.pkl")

# log for debugging
# log = open("log.txt", "a+", buffering=1)

word_vectorizer = HashingVectorizer(decode_error='ignore',
                                    n_features=2 ** 10, non_negative=True)
bigram_vectorizer = HashingVectorizer(analyzer='char', n_features=2 ** 10,
                                      non_negative=True, ngram_range=(1,2))
settings = {"keep_for": timedelta(days=180)}

""" on_post_added will be called when new posts are retrieved
    from other peers, if this functions returns false, the
    content will be rejected (e.g. in the case of spam) and not
    stored by our node """
def on_post_added(args):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        if args["isWhitelabeled"] == True:
            _store_post(args['obj'], cursor)
            conn.commit()
            return {"result": True, "error": None}
        if post.predict(_transform_post(args['obj']))[0] == 'False':
            _store_post(args['obj'], cursor)
            conn.commit()
            return {"result": True, "error": None}
        return {"result": False, "error": None}
    except Exception as e:
        return {"result": None, "error": e.message}

""" OnCommentAdded will be called when new comments are
    retrieved from other peers, if this functions returns
    false, the content will be rejected (e.g. in the case of
    spam) and not stored by our node """
def on_comment_added(args):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        if args["isWhitelabeled"] == True:
            _store_comment(args['obj'], cursor)
            conn.commit()
            return {"result": True, "error": None}
        if comment.predict(_transform_comment(args['obj']))[0] == 'False':
            _store_comment(args['obj'], cursor)
            conn.commit()
            return {"result": True, "error": None}
        return {"result": False, "error": None}
    except Exception as e:
        return {"result": None, "error": e.message}

""" GetContent gives back an ordered array of post hashes of
    suggested content by the curation module """
def get_content(args):
    # TODO: Use lerot to implement this function...?
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    sql = """ SELECT hash, upvotes - downvotes AS score
              FROM posts
              ORDER BY flag, score """
    posts_hash = cursor.execute(sql).fetchall()
    formatted_hashes = []
    for i in posts_hash:
        formatted_hashes.append(i[0])
    return {"result": formatted_hashes, "error": None}

""" FlagContent marks or unmarks hashes as spam. True means
    content is flagged as spam, false means content is not
    flagged as spam """
def flag_content(args):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        post_sql = "SELECT COUNT(hash) FROM posts WHERE hash = ?"
        comment_sql = "SELECT COUNT(hash) FROM comments WHERE hash = ?"
        post_count = cursor.execute(post_sql, [args['hash']]).fetchall()[0][0]
        comment_count = cursor.execute(comment_sql, [args['hash']]).fetchall()[0][0]
        if post_count > 0:
            _flag_post(args, cursor)
            conn.commit()
            return {"result": "ok", "error": None}
        if comment_count > 0:
            _flag_comment(args, cursor)
            conn.commit()
            return {"result": "ok", "error": None}
        return {"result": None, "error": "content not found"}
    except Exception as e:
        return {"result": None, "error": e.message}

""" UpvoteContent is called when user upvotes content """
def upvote_content(args):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        post_sql = "SELECT COUNT(hash) FROM posts WHERE hash = ?"
        comment_sql = "SELECT COUNT(hash) FROM comments WHERE hash = ?"
        post_count = cursor.execute(post_sql, [args['hash']]).fetchall()[0][0]
        comment_count = cursor.execute(comment_sql, [args['hash']]).fetchall()[0][0]
        if post_count > 0:
            _upvote_post(args, cursor)
            conn.commit()
            return {"result": "ok", "error": None}
        if comment_count > 0:
            _upvote_comment(args, cursor)
            conn.commit()
            return {"result": "ok", "error": None}
        return {"result": None, "error": "content not found"}
    except Exception as e:
        return {"result": None, "error": e.message}

""" DownvoteContent is called when user downvotes content """
def downvote_content(args):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        post_sql = "SELECT COUNT(hash) FROM posts WHERE hash = ?"
        comment_sql = "SELECT COUNT(hash) FROM comments WHERE hash = ?"
        post_count = cursor.execute(post_sql, [args['hash']]).fetchall()[0][0]
        comment_count = cursor.execute(comment_sql, [args['hash']]).fetchall()[0][0]
        if post_count > 0:
            _downvote_post(args, cursor)
            conn.commit()
            return {"result": "ok", "error": None}
        if comment_count > 0:
            _downvote_content(args, cursor)
            conn.commit()
            return {"result": "ok", "error": None}
        return {"result": None, "error": "content not found"}
    except Exception as e:
        return {"result": None, "error": e.message}

def close():
    # TODO: save newly trained models
    joblib.dump(post, 'post.pkl')
    joblib.dump(comment, 'comment.pkl')
    return

# INTERNAL FUNCTIONS

""" concatenates content and data for posts and then calls _transform_comment """
def _transform_post(data):
    data['Content'] = data['Content'] + "\n" + data['Title']
    return _transform_comment(data)

""" transform_data accepts a data array and transforms it into
    the model vector format """
def _transform_comment(data):
    """ The data format of the trained schema is:
        data['Content'] transformed by bigram_vectorizer (1024 features)
        data['Content'] transformed by word_vectorizer (1024 features)
        data['Hash'] transformed by word_vectorizer (1024 features)
        data['Alias'] transformed by word_vectorizer (1024 features) """
    content_bigram = bigram_vectorizer.transform([data['Content']])
    content_word = word_vectorizer.transform([data['Content']])
    hash_id = word_vectorizer.transform([data['Hash']])
    alias = word_vectorizer.transform([data['Alias']])
    return sparse.hstack([content_bigram, content_word, hash_id, alias])

# post and comment storage

def _store_post(data, cursor):
    sql = """ INSERT INTO posts(title, content, hash, alias, timestamp)
              VALUES (?, ?, ?, ?, ?) """
    cursor.execute(sql, [data['Title'], data['Content'],
                         data['Hash'], data['Alias'],
                         data['Timestamp']])

def _store_comment(data, cursor):
    sql = """ INSERT INTO comments(content, hash, alias, timestamp)
              VALUES (?, ?, ?, ?) """
    cursor.execute(sql, [data['Content'], data['Hash'], data['Alias'], data['Timestamp']])

# post and comment retrieval

def _retrieve_post(hash_id, cursor):
    sql = """ SELECT title, content, hash, alias, timestamp, flag
              FROM posts
              WHERE hash = ? """
    post_res = cursor.execute(sql, [hash_id]).fetchall()[0]
    return {"Title": post_res[0], "Content": post_res[1],
            "Hash": post_res[2], "Alias": post_res[3],
            "Timestamp": post_res[4], "Flag": post_res[5]}

def _retrieve_comment(hash_id, cursor):
    sql = """ SELECT content, hash, alias, timestamp, flag
              FROM comments
              WHERE hash = ? """
    comment_res = cursor.execute(sql, [hash_id]).fetchall()[0]
    return {"Content": comment_res[0], "Hash": comment_res[1],
            "Alias": comment_res[2], "Timestamp": comment_res[3],
            "Flag": comment_res[4]}

# flagging functions

def _flag_post(args, cursor):
    update_post_sql = "UPDATE posts SET flag = ? WHERE hash = ?"
    cursor.execute(update_post_sql, [args['isFlagged'], args['hash']])
    # train using this example
    X_vec = _transform_post(_retrieve_post(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    post.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def _flag_comment(args, cursor):
    update_comment_sql = "UPDATE comments SET flag = ? WHERE hash = ?"
    cursor.execute(update_comment_sql, [args['isFlagged'], args['hash']])
    X_vec = _transform_comment(_retrieve_comment(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    comment.partial_fit(X_vec, y_vec, classes=['True', 'False'])

# voting functions

def _upvote_post(args, cursor):
    update_post_sql = "UPDATE posts SET upvotes = upvotes + 1 WHERE hash = ?"
    cursor.execute(update_post_sql, [args['hash']])
    X_vec = _transform_post(_retrieve_post(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    post.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def _upvote_comment(args, cursor):
    update_comment_sql = "UPDATE comments SET upvotes = upvotes + 1 WHERE hash = ?"
    cursor.execute(update_comment_sql, [args['hash']])
    X_vec = _transform_comment(_retrieve_comment(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    comment.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def _downvote_post(args, cursor):
    update_post_sql = "UPDATE posts SET downvotes = downvotes + 1 WHERE hash = ?"
    cursor.execute(update_post_sql, [args['hash']])
    X_vec = _transform_post(_retrieve_post(args['hash'], cursor))
    y_vec = np.asarray(['False'])
    post.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def _downvote_comment(args, cursor):
    update_comment_sql = "UPDATE comments SET downvotes = downvotes + 1 WHERE hash = ?"
    cursor.execute(update_comment_sql, [args['hash']])
    X_vec = _transform_comment(_retrieve_comment(args['hash'], cursor))
    y_vec = np.asarray(['False'])
    comment.partial_fit(X_vec, y_vec, classes=['True', 'False'])
