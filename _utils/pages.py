from datetime import datetime
from flask import Markup

def create_page(world, template, submission, current_user):
    revisions = validate_page(template, submission) # fixme, need to add the contents into the template before running this
    if revisions == None:
        template = insert_contents(world, template, submission, current_user, True)
        if template:
            return None, template
        else:
            return "An error occured while saving the page."
    else:
        return revisions, None

# returns page_id of draft after modified
def modify_page(world, draft, submission, new_page, current_user):
    draft = insert_contents(world, draft, submission, current_user, False) # insert the contents but don't save the new draft yet
    submit_value = submission['submit-button']

    if submit_value == 'add_section': # if adding a section
        new_order = draft['sections'][-1]['order'] + 1
        draft['sections'].append(
            {
                'content': "",
                'name': "New Section",
                'order': new_order,
                'required': False
            }
        )

    elif 'delete_section' in submit_value:
        if len(draft['sections']) <= 1:
            return None, 'Page must contain at least one section!'
        id = int(submit_value.replace('delete_section_',''))

        for i in range(id + 1, len(draft['sections'])): # from after the value to be deleted to the end (no info in sections)
            draft['sections'][i]['order'] -= 1

        del draft['sections'][id]

    elif 'add_attribute' in submit_value:
        index = int(submit_value.replace('add_attribute_',''))
        new_pos = len(draft['attributes'][index])
        draft['attributes'][index].insert(new_pos-1,{
            'content': "",
            'name': "",
            'order': new_pos - 1,
            'required': False,
            'table': None
        })
        draft['attributes'][index][-1]['count'] += 1

    elif 'delete_attribute' in submit_value:
        attribute_index, value_index = (submit_value.replace('delete_attribute_','')).split('_')
        attribute_index = int(attribute_index)
        value_index = int(value_index)

        # update order
        for i in range(value_index + 1, len(draft['attributes'][attribute_index]) - 1): # from after the value to be deleted to before the info
            draft['attributes'][attribute_index][i]['order'] -= 1

        del draft['attributes'][attribute_index][value_index]
        draft['attributes'][attribute_index][-1]['count'] -= 1

    elif 'up_attribute' in submit_value or 'down_attribute' in submit_value: # move attribute up or down
        if 'up_attribute' in submit_value:
            attribute_index, value_index = (submit_value.replace('up_attribute_','')).split('_')
            movement = -1
        else: # moving down
            attribute_index, value_index = (submit_value.replace('down_attribute_','')).split('_')
            movement = 1
        attribute_index = int(attribute_index)
        value_index = int(value_index)
        if not (movement == -1 and value_index <= 0) and not (movement == 1 and value_index >= len(draft['attributes'][attribute_index]) - 2): # if within the bounds for movement
            try:
                draft['attributes'][attribute_index][value_index + movement]['order'] -= movement
                draft['attributes'][attribute_index][value_index]['order'] += movement
                temp = draft['attributes'][attribute_index][value_index + movement].copy()
                draft['attributes'][attribute_index][value_index + movement] = draft['attributes'][attribute_index][value_index].copy()
                draft['attributes'][attribute_index][value_index] = temp
            except KeyError: # out of bounds
                pass

    # save and get page_id
    if new_page == 'draft': # if modifying an existing draft
        page_id = current_user.save_draft(world, draft, False)
    else: # a new draft
        page_id = current_user.save_draft(world, draft, True)
    return page_id, None

# returns None if no revisions needed, otherwise returns error message to be displayed to the user
def validate_page(template, submission): #fixme
    revisions = ''
    i = 0
    for section in template['sections']:
        if not section['content']:
            if section['name']:
                revisions += "Section \"" + section['name'] + "\" is blank.<br>"
            else:
                revisions += "Section " + str(i) + " is blank.<br>"
        if not section['name']:
            revisions += "Section " + str(i) + " is missing a name.<br>"
        i += 1
    
    i = 0
    for attribute_index in template['attributes'].keys():
        j = 0
        for value in template['attributes'][attribute_index]:
            if value['order'] < 9999: # if not info
                if not value['content']:
                    if not value['name']:
                        if not template['attributes'][attribute_index][-1]['name']: # attribute section name does NOT exist
                            revisions += "Attribute " + str(j) + " in section " + str(i) + " is blank.<br>"
                        else: # attribute section name exists
                            revisions += "Attribute " + str(j) + " in the \"" + template['attributes'][attribute_index][-1]['name'] + "\" section is blank.<br>"
                    else:
                        if not template['attributes'][attribute_index][-1]['name']: # attribute section name does NOT exist
                            revisions += "Attribute \"" + value['name'] + "\" in section " + str(i) + " is blank.<br>"
                        else: # attribute section name exists
                            revisions += "Attribute \"" + value['name'] + "\" in the \"" + template['attributes'][attribute_index][-1]['name'] + "\" section is blank.<br>"
                if not value['name']:
                    if not template['attributes'][attribute_index][-1]['name']: # attribute section name does NOT exist
                        revisions += "Attribute " + str(j) + " in section " + str(i) + " is missing a name.<br>"
                    else: # attribute section name exists
                        revisions += "Attribute " + str(j) + " in the \"" + template['attributes'][attribute_index][-1]['name'] + "\" section is missing a name.<br>"
            j += 1
        i += 1
    
    if revisions: # revisions needed were found
        return Markup("Please correct the following error(s) before publishing:<br>" + revisions)
    return None

def get_page_id(name):
    id = ""
    for char in name:
        if char in [' ','_','-']:
            id += '-'
        elif char.isalpha():
            id += char.lower()
        elif char.isnumeric():
            id += char
    return id

def insert_contents(world, template, submission, current_user, save):
    for i in range(0, len(template['attributes'])): # add attributes
        for j in range(0, template['attributes'][i][-1]['count']):
            if template['attributes'][i][j]['order'] < 9999: # if not the info value
                #value['name'] = submission['attribute_' + str(i) + '_' + str(j) + '_name']
                template['attributes'][i][j]['content'] = submission['attribute_' + str(i) + '_' + str(j)]
                try:
                    template['attributes'][i][j]['name'] = submission['attribute_' + str(i) + '_' + str(j) + '_name']
                except KeyError:
                    pass

    i = 0
    for section in template['sections']: # add sections
        id = 'section_' + str(i)
        section['content'] = submission[id]
        section['name'] = submission[id + '_name']
        i += 1

    # get old doc ref before potentially changing the category, name, etc.
    old_doc = world.doc_ref.collection(template['info']['collection']).document(template['info']['page_id'])

    # basic info
    old_name = template['info']['name'] # in case name was changed
    template['info']['name'] = submission['page_name']
    template['info']['author'] = current_user.username
    old_category = template['info']['category']
    template['info']['category'] = submission['category']
    old_page_id = template['info']['page_id']
    template['info']['page_id'] = get_page_id(template['info']['name'])
    page_id = template['info']['page_id']
    template['info']['date_updated'] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    # preview
    preview = ""
    max_length = 300
    for i in range(0, len(template['sections'])):
        preview += template['sections'][i]['content']
        if len(preview) > max_length:
            preview = preview[:max_length] + '...'
            break
    template['info']['preview'] = preview

    # image
    if template['info']['img_required']:
        template['info']['img'] = submission['img']
        template['info']['img_attribution'] = submission['img_attribution']

    if save: # if should also store it in the db
        # make or get doc
        doc = world.doc_ref.collection(template['info']['collection']).document(page_id)

        # convert attributes array back into a dict
        temp = {}
        keys = list(template['attributes'].keys())
        for key in keys:
            temp = template['attributes'][key].copy()
            del template['attributes'][key]
            template['attributes'][str(key)] = temp

        if template['info']['published']: # if already published
            if (old_page_id != page_id): # if renamed
                world.doc_ref.collection(template['info']['collection']).document(old_page_id).delete() # delete old document

                # update pages list for world
                curr_pages = world.doc_contents['pages']
                try:
                    curr_pages.pop(old_name)
                except KeyError:
                    pass
                curr_pages[template['info']['name']] = doc
                world.doc_ref.update({"pages": curr_pages})

            if old_category != template['info']['category'] or old_page_id != page_id: # if category was changed or name was changed
                categories = world.doc_contents['categories'] # get current dict of categories
                categories[get_page_id(old_category)]['pages'].remove(old_doc) # remove doc ref from old category page list
                if template['info']['category'] not in categories[get_page_id(template['info']['category'])]['pages']: # double check the doc isn't referenced in the current list
                    categories[get_page_id(template['info']['category'])]['pages'].append(doc) # add doc ref to new category list
                world.doc_ref.update({"categories": categories}) # update stored categories

            # put into recently updated fixme

        else:
            # delete draft doc
            current_user.delete_draft(world, template['info']['page_id'])

            template['info']['page_id'] = page_id
            template['info']['published'] = True
            template['info']['date_created'] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            
            # update doc - fixme if this breaks later when publishing, this line not having doc.set is why
            doc = world.doc_ref.collection(template['info']['collection']).document(page_id) # get new location based on new page id

            categories = world.doc_contents['categories'] # get current dict of categories
            categories[get_page_id(template['info']['category'])]['pages'].append(doc) # add doc ref to category list
            world.doc_ref.update({"categories": categories})

            # add to recently created fixme

        doc.set(template)

    return template

def check_permissions(world, current_user, page):
    if current_user.admin == True:
        return True
    
    if page: # if modifying a page
        try:
            if current_user.username in page['info']['editors']:
                return True
        except KeyError:
            page['info']['editors'] = []
        if current_user.username == page['info']['author']:
            return True
    else: # if modifying a world
        if current_user.username == world.doc_contents['info']['author']:
            return True
        if current_user.username in world.doc_contents['info']['editors']:
            return True
    return False

def format_content(page_refs, content):
    content = content.replace('<','\n').replace('>','&emsp;')
    content = content.replace('/[','<i>').replace(']/','</i>')
    content = content.replace('*[','<b>').replace(']*','</b>')
    content = content.replace('-[','<ul>').replace(']-','</ul>')
    content = content.replace('=[','<ol>').replace(']=','</ol>')

    bold, italics = False, False
    i = 0
    while i < len(content):
        if content[i] == '@' and content[i + 1] == '[': # page link
            j = i + 2
            while content[j] != ']': # get the entire page name
                j += 1
                if j > len(content):
                    break
            content = content[:i] + make_page_ref(page_refs, content[i + 2:j], False) + content[j + 1:]
        elif content[i] == '*': # bullet note
            j = i + 1
            while content[j] != '\n':
                j += 1
                if j > len(content):
                    break
            content = content[:i] + "<li>" + content[i + 1:j] + "</li>" + content[j + 1:]
        i += 1
    content = content.replace('\n','<br>')
    content = Markup(content)
    return content

def make_page_ref(page_refs, page_name, markup = True):
    try:
        linked_page = page_refs[page_name].get().to_dict()
        href = "/display_page/" + linked_page['info']['collection'] + "/" + linked_page['info']['page_id']
    except KeyError:
        href = "/page_not_found"
    href = "<a href=\"" + href + "\">" + page_name + "</a>"
    if markup:
        return Markup(href)
    else:
        return href

def format_template(world, page):
    page_refs = world.doc_contents['pages']
    for i in range(0, len(page['attributes'])):
        for j in range(0, len(page['attributes'][i]) - 1): # all but the last (info) attribute item
            attribute = page['attributes'][i][j]
            if page['attributes'][i][-1]['type'] == 'single':
                attribute['content'] = format_content(page_refs, attribute['content'])
            elif attribute['table']:
                attribute['content'] = make_page_ref(page_refs, attribute['content'].replace('@','').replace('[','').replace(']',''))
    for section in page['sections']:
        section['content'] = format_content(page_refs, section['content'])
    return page['attributes'], page['sections']