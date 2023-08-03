class User():
    username = None
    is_authenticated = False
    is_active = False
    is_anonymous = False
    doc_ref = None
    doc_contents = None
    admin = False

    def activate(self, db, username):
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.doc_ref = db.collection('users').document(username)
        self.doc_contents = self.doc_ref.get().to_dict()

        self.admin = self.doc_contents['admin']

        self.doc_contents['last_login'] = "1" #fixme
        self.doc_ref.set(self.doc_contents) # update

    def get(self):
        return self
    
    def print_username(self):
        print("Requested username:",self.username)
        
    def get_id(self):
        return self.username
    
    def get_doc_contents(self):
        return self.doc_contents

    def save_draft(self, world, draft, new = True):
        if not new: # if saving over an existing draft
            page_id = draft['info']['page_id']
            id = int(page_id.replace(self.username + '-',''))
        else: # need to make a new draft
            if self.doc_contents['drafts'] == None: # if drafts list hasn't been declared yet
                self.doc_contents['drafts'] = []
            if len(self.doc_contents['open_drafts']) == 0: # if no open drafts
                id = len(self.doc_contents['drafts'])
                self.doc_contents['drafts'].append(None) # declare slot for draft
            else:
                id = self.doc_contents['open_drafts'][0] # get soonest open draft slot
                del self.doc_contents['open_drafts'][0] # delete the open slot
        
            page_id = self.username + '-' + str(id)
            draft['info']['page_id'] = page_id
        
        # save
        doc_ref = world.doc_ref.collection('drafts').document(page_id)

        # convert attributes array back into a dict
        temp = {}
        keys = list(draft['attributes'].keys())
        for key in keys:
            temp = draft['attributes'][key].copy()
            del draft['attributes'][key]
            draft['attributes'][str(key)] = temp
        draft['info']['published'] = False

        doc_ref.set(draft)

        self.doc_contents['drafts'][id] = doc_ref
        self.doc_ref.set(self.doc_contents) # save changes

        return page_id
    
    def delete_draft(self, world, page_id):
        id = int(page_id.replace(self.username + '-', ''))
        if len(self.doc_contents['open_drafts']) == 0 and id == len(self.doc_contents['drafts']) - 1: # if deleting last draft and drafts aren't in order
            del self.doc_contents['drafts'][id]
        else:
            self.doc_contents['open_drafts'].append(id)
            self.doc_contents['drafts'][id] = None
        world.doc_ref.collection('drafts').document(page_id).delete()
        self.doc_ref.set(self.doc_contents)
