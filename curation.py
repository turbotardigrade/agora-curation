from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.externals import joblib
from scipy import sparse
from datetime import timedelta
import sqlite3
import warnings
import os, sys

with warnings.catch_warnings():
    warnings.simplefilter("ignore")

os.chdir(sys.path[0])

comment = joblib.load("comment.pkl")
post = joblib.load("post.pkl")

# log for debugging
# log = open("log.txt", "a+", buffering=1)

word_vectorizer = HashingVectorizer(decode_error='ignore',
                                    n_features=2 ** 10, non_negative=True)
bigram_vectorizer = HashingVectorizer(analyzer='char', n_features=2 ** 10,
                                      non_negative=True, ngram_range=(1,2))
settings = {"keep_for": timedelta(days=180)}
""" concatenates content and data for posts and then calls transform_comment """
def transform_post(data):
    data['Content'] = data['Content'] + "\n" + data['Title']
    return transform_comment(data)

""" transform_data accepts a data array and transforms it into
    the model vector format """
def transform_comment(data):
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

def store_post(data, cursor):
    sql = """ INSERT INTO posts(title, content, hash, alias, timestamp)
              VALUES (?, ?, ?, ?, ?) """
    cursor.execute(sql, [data['Title'], data['Content'],
                         data['Hash'], data['Alias'],
                         data['Timestamp']])

def store_comment(data, cursor):
    sql = """ INSERT INTO comments(content, hash, alias, timestamp)
              VALUES (?, ?, ?, ?) """
    cursor.execute(sql, [data['Content'], data['Hash'], data['Alias'], data['Timestamp']])

def retrieve_post(hash_id, cursor):
    sql = """ SELECT title, content, hash, alias, timestamp, flag
              FROM posts
              WHERE hash = ? """
    post = cursor.execute(sql, [hash_id]).fetchall()[0]
    return {"Title": post[0], "Content": post[1], "Hash": post[2], "Alias": post[3], "Timestamp": post[4], "Flag": post[5]}

def retrieve_comment(hash_id, cursor):
    sql = """ SELECT content, hash, alias, timestamp, flag
              FROM comments
              WHERE hash = ? """
    comment = cursor.execute(sql, [hash_id]).fetchall()[0]
    return {"Content": comment[0], "Hash": comment[1], "Alias": comment[2], "Timestamp": comment[3], "Flag": comment[4]}

""" on_post_added will be called when new posts are retrieved
    from other peers, if this functions returns false, the
    content will be rejected (e.g. in the case of spam) and not
    stored by our node """
def on_post_added(args):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        if args["isWhitelabeled"] == True:
            store_post(args['obj'], cursor)
            conn.commit()
            return {"result": True, "error": None}
        if post.predict(transform_post(args['obj'])) == 'False':
            store_post(args['obj'], cursor)
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
            store_comment(args['obj'], cursor)
            conn.commit()
            return {"result": True, "error": None}
        if post.predict(transform_comment(args['obj'])) == 'False':
            store_comment(args['obj'], cursor)
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
    sql = """ SELECT hash
              FROM posts
              ORDER BY flag """
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
            ret = flag_post(args, cursor)
            conn.commit()
            return ret
        if comment_count > 0:
            ret = flag_comment(args, cursor)
            conn.commit()
            return ret
        return {"result": None, "error": "content not found"}
    except Exception as e:
        return {"result": None, "error": e.message}

def flag_post(args, cursor):
    update_post_sql = "UPDATE posts SET flag = ? WHERE hash = ?"
    cursor.execute(update_post_sql, [args['isFlagged'], args['hash']])
    # train using this example
    X_vec = transform_post(retrieve_post(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    post.partial_fit(X_vec, y_vec, classes=[1, 0])

def flag_comment(args, cursor):
    update_comment_sql = "UPDATE comments SET flag = ? WHERE hash = ?"
    cursor.execute(update_comment_sql, [args['isFlagged'], args['hash']])
    X_vec = transform_comment(retrieve_comment(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    comment.partial_fit(X_vec, y_vec, classes=['True', 'False'])

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
            ret = upvote_post(args, cursor)
            conn.commit()
            return ret
        if comment_count > 0:
            ret = upvote_comment(args, cursor)
            conn.commit()
            return ret
        return {"result": None, "error": "content not found"}
    except Exception as e:
        return {"result": None, "error": e.message}

def upvote_post(args, cursor):
    update_post_sql = "UPDATE posts SET upvotes = upvotes + 1 WHERE hash = ?"
    cursor.execute(update_post_sql, [args['hash']])
    X_vec = transform_post(retrieve_post(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    post.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def upvote_comment(args, cursor):
    update_comment_sql = "UPDATE comments SET upvotes = upvotes + 1 WHERE hash = ?"
    cursor.execute(update_comment_sql, [args['hash']])
    X_vec = transform_comment(retrieve_comment(args['hash'], cursor))
    y_vec = np.asarray(['True' if args['isFlagged'] else 'False'])
    comment.partial_fit(X_vec, y_vec, classes=['True', 'False'])

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
            ret = downvote_post(args, cursor)
            conn.commit()
            return ret
        if comment_count > 0:
            ret = downvote_content(args, cursor)
            conn.commit()
            return ret
        return {"result": None, "error": "content not found"}
    except Exception as e:
        return {"result": None, "error": e.message}

def downvote_post(args, cursor):
    update_post_sql = "UPDATE posts SET downvotes = downvotes + 1 WHERE hash = ?"
    cursor.execute(update_post_sql, [args['hash']])
    X_vec = transform_post(retrieve_post(args['hash'], cursor))
    y_vec = np.asarray(['False'])
    post.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def downvote_comment(args, cursor):
    update_comment_sql = "UPDATE comments SET downvotes = downvotes + 1 WHERE hash = ?"
    cursor.execute(update_comment_sql, [args['hash']])
    X_vec = transform_comment(retrieve_comment(args['hash'], cursor))
    y_vec = np.asarray(['False'])
    comment.partial_fit(X_vec, y_vec, classes=['True', 'False'])

def close():
    # TODO: save newly trained warnings
    return
