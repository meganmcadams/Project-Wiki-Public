class World():
    name = ""

    doc_ref = ""
    doc_contents = None

    def activate(self, db, world_name):
        self.name = world_name
        self.doc_ref = db.collection('worlds').document(world_name)
        self.doc_contents = self.doc_ref.get().to_dict()