class mypymesh:
    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces

    @staticmethod
    def boolean(_other, _operation):
        return mypymesh([], [])

    @property
    def volume(self):
        return 0
