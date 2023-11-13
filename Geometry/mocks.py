class mypymesh:
    class Mesh:
        def __init__(self, vertices, faces):
            self.vertices = vertices
            self.faces = faces

        @property
        def volume(self):
            return 0

    @staticmethod
    def boolean(mesh_a, mesh_b, operation):
        return mypymesh.Mesh([], [])

    @staticmethod
    def form_mesh(vertices, faces):
        return mypymesh.Mesh(vertices, faces)
