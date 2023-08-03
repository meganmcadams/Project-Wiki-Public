from bcrypt import checkpw, gensalt, hashpw

def login_check(db, username, password):
    try:
        doc = db.collection('users').document(username).get().to_dict()
        encoded = password.encode('utf-8')
        if checkpw(encoded, doc['password']):
            return True
        else:
            return False
    except:
        doc = db.collection('users').document(username).get().to_dict()
        encoded = password.encode('utf-8')
        return False

def create_user(db, submission):

    # validate input
    # get inputs
    username = submission['username']
    password = submission['password']
    email = submission['email']
    confirm_password = submission['password_confirm']

    # username
    try:
        if db.collection('users').document(username).get().to_dict():
            return "Username \"" + str(username) + "\" already taken!"
    except:
        pass
    if str(username).isnumeric():
        return "Username must contain at least one letter."
    if str(username)[0].isnumeric():
        return "Username must start with a letter."
    if len(username) < 5:
        return "Username must be at least 5 characters long."
    
    # password
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if password != confirm_password:
        return "Passwords do not match."
    
    if '@' not in email:
        return "Please enter a valid email."

    # insert into db
    salt = gensalt()
    hash = hashpw(password.encode('utf-8'), salt)
    doc = db.collection("users").document(username)
    doc.set(
        {
            "username": username,
            "password": hash,
            "admin": False,
            "drafts": None,
            "date_joined": None #fixme
        }
    )
    return None
