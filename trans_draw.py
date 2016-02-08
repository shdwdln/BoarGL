from __future__ import division

import os
import numpy as np
A = np.array
import math as m
import OpenGL.GL as gl
#import OpenGL.GLUT as glut
import transforms as trans

#float32 numpy array cast
flar = lambda a: np.array(a, dtype = np.float32)

def load_text(filename):
    with open(filename) as f:
        data = f.read()
        return data
    return None

def geomBufferTR(g):
    # like the scrunlib version, but using 4-element position
    vtype = [('a_position', np.float32, 4),
             ('a_texcoord', np.float32, 2),
             ('a_normal'  , np.float32, 3),
             ('a_color',    np.float32, 4)]


    itype = np.uint32
    p = g.verts
    n = g.norms #[g.norms[x] for x in range(0, 36, 6)]
    c = g.cols
    t = g.tex_coord[0]


    faces_p = g.inds.flatten()
    nv = len(faces_p)
    faces_c = faces_p
    faces_t = g.tex_coord_ind[0].flatten()
    faces_n = faces_p

    vertices = np.zeros(nv,vtype)
    try:
        vertices['a_position'] = p[faces_p]
        vertices['a_normal'] = n[faces_n]
        vertices['a_color'] = c[faces_c]
        vertices['a_texcoord'] = t[faces_t]
    except Exception, e:
        print "verts(p): %s" % str(p)
        print "inds: %s" % str(faces_p)
        print "normals(n) %s" % str(n)
        print "ni: %s" % str(faces_n)
        print "faces_c: %s" % str(faces_c)
        print "c: %s" % str(c)
        print "faces_t: %s" % str(faces_t)
        raise

    filled = np.array(range(nv), dtype=np.uint32)

    return vertices, filled

class ProgBundle(object):
    def __init__(self, vershade, fragshade):
        self.vershade = load_text(vershade)
        self.fragshade = load_text(fragshade)
        self.program = Program(self.vershade, self.fragshade)

def atcat(attr, VB1, VB2):
    "build a degenerate triangle"
    a = getattr(VB1, attr)
    c = getattr(VB2, attr)
    b = [a[-1], c[0]]
    return np.concatenate([a, b, c])

nrm = lambda a: a / np.linalg.norm(a)

class ProgPlex(object): # sets items in multiple bundles.  might be handled by uniform blocks better?
    def __init__(self, bundles = []):
        self.bundles = bundles
    def __setitem__(self, index, value):
        for bundle in self.bundles:
            bundle.program[index] = value

class VertexBundle(object): # converts a set of verts, norms, cols, uvs into a packed data structure
    @classmethod
    def normals_bundle(cls, vb, color = [1, 1, 1, 1]):
        verts = []
        norms = []
        cols = []
        uvs = []
        for i, vert in enumerate(vb.verts):
            p0 = vert
            p1 = vert + .1*vb.norms[i]
            verts = verts + [p0, p1]
            norms = norms + [nrm(vert), nrm(vert)]
            cols = cols + [color, color]
            uvs = uvs + [vb.tk[i], vb.tk[i]]
        return VertexBundle(verts, norms, cols, uvs)

    @classmethod
    def glue_strips(cls, VB1, VB2):
        "glue two triangle strips together with degenerate triangles"
        v = atcat("verts", VB1, VB2)
        c = atcat("cols", VB1, VB2)
        n = atcat("norms", VB1, VB2)
        u = atcat("tk", VB1, VB2)
        return VertexBundle(v, n, c, u)
    def __init__(self, verts, norms, cols, uv, inds = None, uvb = None):
        "ready a bunch of data for buffers"
        if inds == None:
            inds = list(range(len(verts)))
        self.verts = A(verts, dtype=np.float32)
        self.norms = A(norms, dtype=np.float32)
        self.cols = A(cols, dtype=np.float32)
        self.inds = A(inds)
        self.tk = uv
        # possibility of two sets of text coords, eventually -- front and back FIXME:
        self.tex_coord = A([uv], dtype=np.float32)
        self.tex_coord_ind = A([inds])
    def bufferize(self):
        "actually package buffered data for GL"
        v, f = geomBufferTR(self)
        self.cooked_faces = v
        self.cooked_ind = f


class Drawable(object):
    def __init__(self, vershade, fragshade):
        self.vershade = load_text(vershade)
        self.fragshade = load_text(fragshade)
        self.program = Program(self.vershade, self.fragshade)
    def package(self, verts, norms, cols, inds, uv):
        self.verts = A(verts, dtype=np.float32)
        self.norms = A(norms, dtype=np.float32)
        self.cols = A(cols, dtype=np.float32)
        self.inds = A(inds)
        self.tk = uv
        self.tex_coord = A([uv], dtype=np.float32)
        self.tex_coord_ind = A([inds])
        #if 1:
        #    return
        v, f = geomBufferTR(self)
        self.cooked_faces = v
        self.cooked_ind = f
        self.VertBuf = VertexBuffer(v)
        self.IndBuf = IndexBuffer(f)
    def load_tex(self, path):
        im = cv2.imread(path)
        im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
        texture = Texture2D(im)
        return texture

