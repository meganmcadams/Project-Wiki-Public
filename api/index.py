from flask import Flask, request, render_template, url_for, redirect
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from firebase_admin import credentials, firestore, initialize_app
from _utils.users import login_check, create_user
from _utils.load_db import load_sections, load_events, load_template, load_page_options
from _utils.pages import create_page, modify_page, check_permissions, get_page_id, format_template
from _utils.templates import create_template, modify_template
from _utils.User import User
from _utils.World import World

# Initialize Flask app
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
user = User()

# load secret key
f = open('secret_key.txt')
app.secret_key = f.read()
f.close()

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
fs_app = initialize_app(cred)
db = firestore.client()

# LOAD DB
global world_name
world_name = 'isles-of-lloryan'
world = World()

'''
world.activate(db, world_name)
contents = world.doc_ref.collection('characters').document('saraia-dreamdew').get().to_dict()
new_doc = world.doc_ref.collection('character').document('saraia-dreamdew')
print(contents)
new_doc.set(contents)

world.update({"home":{

        "recently_posted": [
            None, None, None, None, None, None, None, None, None, None
        ],
        "recently_updated": [
            None, None, None, None, None, None, None, None, None, None
        ]
                                  
    }})
'''


# PAGES
@app.route('/testing')
def page_testing():
    world.activate(db, world_name)
    pages = world.doc_contents['pages']
    return render_template('testing.html', navbar=True, page_options=load_page_options(db, world_name, world),
                           pages=pages)

@app.route('/')
def page_home():
    world.activate(db, world_name)
    
    return render_template('home.html', navbar=True, page_options=load_page_options(db, world_name, world))
    
@app.route('/create_account/')
def page_create_account():
    return render_template('create_account.html', navbar=False, message='') #fixme - copy from laptop

@app.route('/login/')
def page_login():
    return render_template('login.html', navbar=False, page_options=load_page_options(db, world_name), message="")

@app.route('/character/<character_id>')
def page_character(character_id):
    world.activate(db, world_name)
    character = world.doc_ref.collection('characters').document(character_id)
    sections = load_sections(character)
    sections_len = len(sections)
    character = character.get().to_dict()
    return render_template('character.html', navbar=True, page_options=load_page_options(db, world_name, world),
                           character=character, sections=sections, sections_len=sections_len, character_id=character_id)

@app.route('/attributions/')
def page_attributions():
    world.activate(db, world_name)
    return render_template('attributions.html', navbar=True, page_options=load_page_options(db, world_name, world))

@app.route('/timeline/')
def page_timeline():
    world.activate(db, world_name)
    events, campaigns = load_events(world)
    return render_template('timeline.html', navbar=True, page_options=load_page_options(db, world_name, world), 
                           events=events, events_len=len(events))

@app.route('/pages/<category>/')
def page_pages(category):
    world.activate(db, world_name)
    navbar = world.doc_contents['navbar']

    category_id = get_page_id(category)
    pages = world.doc_contents['categories'][category_id]['pages']
    for i in range(0, len(pages)):
        pages[i] = pages[i].get().to_dict()

    return render_template('pages.html', navbar=True, page_options=load_page_options(db, world_name), 
                           pages=pages, category=category)

@app.route('/denied/')
def page_denied():
    return render_template('denied.html', navbar=True, page_options=load_page_options(db, world_name))

@app.errorhandler(404)
@app.route('/page_not_found/<e>')
def page_not_found(e = None):
    return render_template('page_not_found.html', navbar=False, page_options=load_page_options(db, world_name))

@app.errorhandler(401)
@app.route('/permission_denied/<e>')
def page_permission_denied(e = None):
    return render_template('permission_denied.html', navbar=False, page_options=load_page_options(db, world_name))

@app.route('/logout/')
@login_required
def page_logout():
    logout_user()
    return page_home()

@app.route('/create_page/<location>/<template_name>/<new_page>')
@login_required
def page_create_page(location, template_name, new_page, message=""):
    world.activate(db, world_name)
    template = load_template(world, location, template_name)
    categories = world.doc_contents['categories']
    pages = world.doc_contents['pages']
    tables = world.doc_contents['tables']

    # check permissions
    if new_page != 'new':
        if not check_permissions(world, current_user, template):
            return page_denied()

    return render_template('create_page.html', navbar=True, page_options=load_page_options(db, world_name, world, ['create_page']), 
                           template=template, template_name=template_name, location=location, new_page=new_page, 
                           sections_len=len(template['sections']), attributes_len = len(template['attributes']),message=message,
                           categories=categories, pages=pages, tables=tables)

@app.route('/create_template/<location>/<template_name>/<new_template>')
@login_required
def page_create_template(location, template_name, new_template, message=""):
    world.activate(db, world_name)

    # check permissions
    if not check_permissions(world, current_user, None):
        return page_denied()

    if new_template == 'new':
        template = load_template(db.collection('global').document('sample-template'), 'templates', 'template')
    else: # draft or existing
        template = load_template(world, location, template_name)
    return render_template('create_template.html', navbar=True, page_options=load_page_options(db, world_name), 
                           template=template, template_name=template_name, location=location, new_template=new_template, 
                           sections_len=len(template['sections']), attributes_len = len(template['attributes']),message=message)

@app.route('/display_page/<location>/<page_id>')
def page_display_page(location, page_id):
    world.activate(db, world_name)
    template = load_template(world, location, page_id)
    attributes, sections = format_template(world, template)
    return render_template('display_page.html', navbar=True, page_options=load_page_options(db, world_name), 
                           template=template, page_id=page_id, location=location, 
                           attributes=attributes, sections=sections )

# FUNCTIONS
@app.route('/create_page/<location>/<template_name>/<new_page>', methods = ['POST', 'GET'])
@login_required
def post_create_page(location, template_name, new_page):
    world.activate(db, world_name)
    template = load_template(world, location, template_name)

    # check permissions
    if new_page != 'new':
        if not check_permissions(world, current_user, template):
            return page_denied()

    if request.method == 'POST':
        if request.form['submit-button'] == 'publish':
            revisions, template = create_page(world, template, request.form, current_user)
            if revisions == None: # no revisions needed
                return page_display_page(template['info']['collection'], template['info']['page_id'])
            else:
                return page_create_page('drafts', template['info']['page_id'], 'draft', message=revisions)
        else: # add or remove a section/attribute or save as a draft
            page_id, revisions = modify_page(world, template, request.form, new_page, current_user) # fixme
            if page_id != None: # if was successful
                return page_create_page('drafts', page_id, 'draft')
            else:
                return page_create_page('drafts', page_id, 'draft', message=revisions)
            
@app.route('/create_template/<location>/<template_name>/<new_template>', methods = ['POST', 'GET'])
@login_required
def post_create_template(location, template_name, new_template):
    world.activate(db, world_name)
    if new_template == 'new': # if new
        template = load_template(db.collection('global').document('sample-template'), 'templates', 'template')
    else:
        template = load_template(world, location, template_name)
    if request.method == 'POST':
        if request.form['submit-button'] == 'publish':
            revisions = create_template(world, template, request.form, current_user)
            if revisions == None: # no revisions needed
                pass # fixme
            else:
                return page_create_template('drafts', template['info']['page_id'], 'draft', message=revisions)
        else: # add or remove a section/attribute
            page_id, revisions = modify_template(world, template, request.form, new_template, current_user)
            if page_id != None: # if was successful
                return page_create_template('drafts', page_id, 'draft')
            else:
                return page_create_template('drafts', page_id, 'draft', message=revisions)

@login_manager.user_loader
def load_user(user_id):
    user = User()
    try:
        #doc = db.collection('users').document(user_id).get().to_dict()
        user.activate(db, user_id)
        return user
    except:
        return None

@app.route("/login/", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('page_home'))
    if login_check(db, request.form['username'], request.form['password']):
        remember_me = request.form.get('remember_me') # fixme
        if remember_me == 'on':
            remember_me = True
        else:
            remember_me = False

        # fetch user using the 'username' property
        # refer to the datastore-entity documentation for more
        user.activate(db, request.form['username'])

        if login_user(user, remember=remember_me):
            user.authenticated = True
            return redirect(url_for('page_home'))
        else:
            return render_template('login.html', navbar=None, page_options=load_page_options(db, world_name), 
                                   message="An error occurred while trying to log you in. Please try again.")

    else:
        return render_template('login.html', navbar=None, page_options=load_page_options(db, world_name), 
                               message="Incorrect username or password. Please try again.")
        
@app.route('/create_account/', methods = ['POST', 'GET'])
def create_account_method():
    if request.method == 'POST':
        if create_user(db, request.form['username'], request.form['password']):
            return render_template('home.html', navbar=None, page_options=load_page_options(db, world_name))
        else:
          return render_template('login.html', navbar=None, page_options=load_page_options(db, world_name), 
                                 message="")

#if __name__ == '__main__':
#    import os
#    port = int(os.environ.get('PORT', 8080))
#    app.run(debug=True, threaded=False, host='0.0.0.0', port=port)
