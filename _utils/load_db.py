from flask import Markup
from _utils.World import World
#from datetime import datetime

def load_sections(page_doc):
    sections = page_doc['sections']
    for section in sections:
        section['content'] = Markup(section['content'])
    return bubble_sort(sections, 'order')

def load_events(world):
    events = []
    campaigns = []
    docs = world.doc_ref.collection('events').get()
    for doc in docs:
        doc = doc.to_dict()
        doc['short_desc'] = doc['desc'][0:200]
        if len(doc['desc']) > 200:
            doc['short_desc'] += '...'
        events.append(doc)
        if doc['type'] == 'campaign':
            campaigns.append(doc)
    return bubble_sort(events, 'date_value', False), bubble_sort(campaigns, 'date_value', False)

def load_character_options(db):
    doc = db.doc_ref.collection('global').document('options').get()
    doc = doc.to_dict()
    return doc['races']

def bubble_sort(list_of_dicts, orderby, asc=True):
    swapped = True
    while swapped:
        swapped = False
        for i in range(0, len(list_of_dicts) - 1):
            swap = False

            try: # correction for no order key
                temp = list_of_dicts[i][orderby]
            except KeyError:
                list_of_dicts[i]['order'] = 9999
            try: # correction for no order key
                temp = list_of_dicts[i + 1][orderby]
            except KeyError:
                list_of_dicts[i + 1]['order'] = 9999

            if asc:
                if list_of_dicts[i][orderby] > list_of_dicts[i + 1][orderby]:
                    swap = True
            else: # descending
                if list_of_dicts[i][orderby] < list_of_dicts[i + 1][orderby]:
                    swap = True
            if swap:
                temp = list_of_dicts[i]
                list_of_dicts[i] = list_of_dicts[i + 1]
                list_of_dicts[i + 1] = temp
                swapped = True
    return list_of_dicts

def get_templates(world):
    docs = world.doc_ref.document('templates')
    return [doc.get().to_dict()['name'] for doc in docs]

def load_template(world, location, template_name):
    if template_name == 'template': # passed the sample template doc itself
        template_ref = world.doc_ref
    else: # passed a world
        template_ref = world.doc_ref.collection(location).document(template_name)
    template = template_ref.get().to_dict()
    keys = list(template['attributes'].keys())
    for key in keys:
        temp = template['attributes'][key].copy()
        del template['attributes'][key]
        template['attributes'][int(key)] = temp
    info = template['info']
    info['views'] += 1
    template_ref.update({"info": info})
    return template

def to_dict(dict, doc):
    cols = doc.collections()
    found_col = False
    for col in cols:
        found_col = True
        if col.id != 'storage':
            dict[col.id] = {}
        docs = col.list_documents()
        for d in docs:
            if col.id != 'storage':
                dict[col.id][d.id] = to_dict({}, d)
            else:
                dict[d.id] = to_dict({}, d)
    if found_col:
        return dict
    else: # leaf
        return doc.get().to_dict()
    
def move_backwards(document):
    cols = document.collections()
    new_col = document.collection('storage')
    for col in cols:
        docs = col.list_documents()
        for doc in docs:
            doc = doc.get().to_dict()
            new_doc = new_col.document(doc['name'].lower().replace(' ','-').replace('(','').replace(')',''))
            new_doc.set(doc)

def load_page_options(db, world_name, world=None, scripts=[]):
    page_options = {}
    if not world:
        world = World()
        world.activate(db, world_name)
    page_options['world'] = world.doc_ref
    page_options['navbar'] = world.doc_contents['navbar']
    worlds = db.collection('global').document('options').get().to_dict()['worlds']
    page_options['default_worlds'] = worlds['defaults']
    page_options['user_worlds'] = worlds['user-made']
    try:
        page_options['world_name'] = worlds['defaults'][world_name]['name']
    except KeyError:
        page_options['world_name'] = worlds['user-made'][world_name]['name']
    page_options['scripts'] = scripts
    return page_options