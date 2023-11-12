import pymesh

vertices = [
    [0, 0, 0],
    [1, 0, 0],
    [1, 1, 0],
    [0, 1, 0]

]

faces = [
    [0, 1, 2],
    [0, 2, 3]
]

mesh = pymesh.form_mesh(vertices, faces)
