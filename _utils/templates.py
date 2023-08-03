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

def create_template(world, template, submission, current_user):
    revisions = validate_template(template)
    if revisions == None:
        if template_insert_contents(world, template, submission, current_user, True):
            return None
        else:
            return "An error occured while saving the template."
    else:
        return revisions

# returns page_id of draft after modified
def modify_template(world, draft, submission, new_page, current_user):
    draft = template_insert_contents(world, draft, submission, current_user, False) # insert the contents but don't save the new draft yet
    submit_value = submission['submit-button']

    if submit_value == 'add_section': # if adding a section
        if len(draft['sections']) <= 0:
            new_order = 0
        else:
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
            return None, 'Page must contain at least one section!' #fixme - we don't even make it this far
        id = int(submit_value.replace('delete_section_',''))

        for i in range(id + 1, len(draft['sections'])): # from after the value to be deleted to the end (no info in sections)
            draft['sections'][i]['order'] -= 1

        del draft['sections'][id]

    elif 'add_attribute_section' in submit_value:
        new_index = len(draft['attributes'])
        if len(draft['attributes']) <= 0:
            new_order = 0
        else:
            new_order = draft['attributes'][new_index - 1][-1]['order'] + 1
        draft['attributes'][new_index] = [] # add the new attribute
        draft['attributes'][new_index].append( # create first attribute
            { 
                'content': "",
                'name': "",
                'order': new_order,
                'table': None
            }
        )
        draft['attributes'][new_index].append( # info
            {
                'count': 1,
                'name': "",
                'order': 9999,
                'required': False,
            }
        )
        if 'single' in submit_value: # adding a single attribute section
            draft['attributes'][new_index][1]['type'] = 'single'
        else: # adding a list attribute section
            draft['attributes'][new_index][0]['required'] = False # add the required key
            draft['attributes'][new_index][1]['type'] = 'list'

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

    elif 'delete_attribute_section' in submit_value:
        attribute_index = int(submit_value.replace('delete_attribute_section_',''))
        length = len(draft['attributes'])

        del draft['attributes'][attribute_index]
        # update order
        temp_values = list(draft['attributes'].values())
        deleted = False
        for i in range(attribute_index, len(temp_values)):
            draft['attributes'][i] = draft['attributes'][i + 1]
            deleted = True
        if deleted:
            del draft['attributes'][len(temp_values)]

    elif 'delete_attribute' in submit_value:
        attribute_index, value_index = (submit_value.replace('delete_attribute_','')).split('_')
        attribute_index = int(attribute_index)
        value_index = int(value_index)

        # update order
        for i in range(value_index + 1, len(draft['attributes'][attribute_index]) - 1): # from after the value to be deleted to before the info
            if draft['attributes'][attribute_index][i]['order'] < 9999: # if not the info
                draft['attributes'][attribute_index][i]['order'] -= 1

        del draft['attributes'][attribute_index][value_index]
        draft['attributes'][attribute_index][-1]['count'] -= 1

    elif 'up_attribute_section' in submit_value or 'down_attribute_section' in submit_value: # move attribute up or down
        if 'up_attribute' in submit_value:
            attribute_index = int(submit_value.replace('up_attribute_section_',''))
            movement = -1
        else: # moving down
            attribute_index = int(submit_value.replace('down_attribute_section_',''))
            movement = 1
        if not (movement == -1 and attribute_index <= 0) and not (movement == 1 and attribute_index >= len(draft['attributes']) - 1): # if within the bounds for movement
            try:
                temp = draft['attributes'][attribute_index + movement].copy()
                draft['attributes'][attribute_index + movement] = draft['attributes'][attribute_index].copy()
                draft['attributes'][attribute_index] = temp
            except KeyError: # out of bounds
                pass

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

def validate_template(submission):
    return None

def template_insert_contents(world, template, submission, current_user, save):
    try:
        page_id = template['info']['page_id']
        if not page_id:
            page_id = get_page_id(submission['page_name'])
    except:
        page_id = get_page_id(submission['page_name'])

    for i in range(0, len(template['attributes'])): # add attributes
        template['attributes'][i][-1]['name'] = submission['attribute_section_' + str(i) + '_name']
        for j in range(0, template['attributes'][i][-1]['count']): # for attribute in attribute section
            if template['attributes'][i][j]['order'] < 9999: # if not the info value
                id = 'attribute_' + str(i) + '_' + str(j)
                template['attributes'][i][j]['name'] = submission[id + '_name']
                if template['attributes'][i][-1]['type'] != 'single': # if has a required key
                    try:
                        template['attributes'][i][j]['required'] = submission[id + '_required']
                    except KeyError:
                        template['attributes'][i][j]['required'] = False

    i = 0
    for section in template['sections']: # add sections
        id = 'section_' + str(i)
        section['name'] = submission[id + '_name']
        try:
            section['required'] = submission[id + '_required']
        except KeyError:
            section['required'] = False
        i += 1

    try:
        template['info']['img_required'] = submission['img_required']
    except KeyError:
        template['info']['img_required'] = False

    template['info']['name'] = submission['page_name']
    template['info']['author'] = current_user.username
    template['info']['template'] = get_page_id(template['info']['name']) # store name of template
    template['info']['category'] = None

    if save: # if should also store it in the db
        # delete draft doc
        current_user.delete_draft(world, template['info']['page_id'])

        # convert attributes array back into a dict
        temp = {}
        keys = list(template['attributes'].keys())
        for key in keys:
            temp = template['attributes'][key].copy()
            del template['attributes'][key]
            template['attributes'][str(key)] = temp

        if template['info']['published']: # if already published
            page_id = template['info']['page_id']
            new_page_id = get_page_id(template['info']['name'])
            if (new_page_id != page_id): # if renamed
                doc = world.doc_ref.collection(template['info']['collection']).document(page_id).delete() # delete old document
                page_id = new_page_id
                template['info']['page_id'] = page_id # store new page id
        else:
            page_id = get_page_id(template['info']['name'])
            template['info']['page_id'] = page_id
            template['info']['published'] = True
        doc = world.doc_ref.collection(template['info']['collection']).document(page_id)
        doc.set(template)

    return template