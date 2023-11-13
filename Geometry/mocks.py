class mypymesh:
    class Mesh:
        def __init__(self, vertices, faces):
            self.vertices = vertices
            self.faces = faces

        @property
        def volume(self):
            return 0

    @staticmethod
    def boolean(_other, _operation):
        return mypymesh.Mesh([], [])
