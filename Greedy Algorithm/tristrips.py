import sys, os, math, random

try:  # PyOpenGL
    from OpenGL.GL import *
except:
    print('Error: PyOpenGL has not been installed.')
    sys.exit(0)

try:  # GLFW
    import glfw
except:
    print('Error: GLFW has not been installed.')
    sys.exit(0)


# Globals

window = None
windowWidth = 1000  # window dimensions
windowHeight = 1000

minX = None  # range of vertices
maxX = None
minY = None
maxY = None

r = 0.008  # point radius as fraction of window size

allVerts = []  # all triangle vertices
lastKey = None  # last key pressed

showForwardLinks = True
outlineTriangles = True
showTriangleBackground = True

# Colour
class Colour(object):
    def __init__(self):
        self.nextColourIndex = 0
        self.colours = [(.4, .2, .7), (.6, .6, 0), (.6, 0, .6), (1, 0, 0), (1, 0, 1), (0, 0, 1),
                        (0, 1, 1), (0, 1, 0), (1, 1, 0), (.6, 0, 0), (0, 0, .6), (0, .6, 0)]

    def nextColour(self):
        t = self.colours[self.nextColourIndex]
        self.nextColourIndex = (self.nextColourIndex + 1) % len(self.colours)
        return (t[0] + random.uniform(-0.3, 0.3),
                t[1] + random.uniform(-0.3, 0.3),
                t[2] + random.uniform(-0.3, 0.3))


colour = Colour()


# Triangle class
class Triangle(object):
    nextID = 0

    def __init__(self, verts):
        self.verts = verts  # 3 vertices (each an index into allVerts)
        self.adjTris = []  # adjacent triangles
        self.isOnStrip = False
        self.nextTri = None  # next triangle on strip
        self.prevTri = None  # previous triangle on strip
        self.highlight1 = False  # highlight color 1
        self.highlight2 = False  # highlight color 2
        self.centroid = (sum([allVerts[i][0] for i in self.verts]) / len(self.verts),
                         sum([allVerts[i][1] for i in self.verts]) / len(self.verts))
        self.colour = colour.nextColour()
        self.id = Triangle.nextID
        Triangle.nextID += 1

    def __repr__(self):
        return 'tri-%d' % self.id

    def draw(self):
        if self.highlight1 or self.highlight2:
            glColor3f(0.9, 0.9, 0.4) if self.highlight1 else glColor3f(1, 1, 0.8)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glBegin(GL_POLYGON)
            for i in self.verts:
                glVertex2f(allVerts[i][0], allVerts[i][1])
            glEnd()

        if showTriangleBackground:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glColor3f(*self.colour)
            glBegin(GL_POLYGON)
            for i in self.verts:
                glVertex2f(allVerts[i][0], allVerts[i][1])
            glEnd()

        if outlineTriangles:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3f(0, 0, 0)
            glBegin(GL_LINE_LOOP)
            for i in self.verts:
                glVertex2f(allVerts[i][0], allVerts[i][1])
            glEnd()

    def drawPointers(self):
        glColor3f(1, 1, 1) if showTriangleBackground else glColor3f(0, 0, 0)
        if showForwardLinks and self.nextTri:
            drawSegment(self.centroid[0], self.centroid[1],
                        self.nextTri.centroid[0], self.nextTri.centroid[1])
        if not showForwardLinks and self.prevTri:
            drawSegment(self.centroid[0], self.centroid[1],
                        self.prevTri.centroid[0], self.prevTri.centroid[1])
        if not self.nextTri and not self.prevTri:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glBegin(GL_POLYGON)
            for i in range(100):
                theta = 3.14159 * i / 50.0
                glVertex2f(self.centroid[0] + 0.5 * r * math.cos(theta),
                           self.centroid[1] + 0.5 * r * math.sin(theta))
            glEnd()

    def containsPoint(self, point):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

        v1 = allVerts[self.verts[0]]
        v2 = allVerts[self.verts[1]]
        v3 = allVerts[self.verts[2]]

        d1 = sign(point, v1, v2)
        d2 = sign(point, v2, v3)
        d3 = sign(point, v3, v1)

        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

        return not (has_neg and has_pos)


def drawSegment(x0, y0, x1, y1):
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x1, y1)
    glEnd()


# Additional functions: turn, buildTristrips, display, etc.
# Key callback function
def keyCallback(window, key, scancode, action, mods):
    global lastKey, showForwardLinks, outlineTriangles, showTriangleBackground
    if action == glfw.PRESS:
        if key == ord('F'):  # toggle forward/backward link display
            showForwardLinks = not showForwardLinks
        elif key == ord('O'):  # toggle triangle outlining
            outlineTriangles = not outlineTriangles
        elif key == ord('B'):  # toggle triangle coloured background
            showTriangleBackground = not showTriangleBackground
        else:
            lastKey = key


def mouseButtonCallback(window, btn, action, keyModifiers):
    if action == glfw.PRESS:
        x, y = glfw.get_cursor_pos(window)
        wx = (x - 0) / float(windowWidth) * (windowRight - windowLeft) + windowLeft
        wy = (windowHeight - y) / float(windowHeight) * (windowTop - windowBottom) + windowBottom
        selectedTri = None
        for tri in allTriangles:
            if tri.containsPoint([wx, wy]):
                selectedTri = tri
                break
        if selectedTri:
            selectedTri.highlight1 = not selectedTri.highlight1
            print('%s with adjacent %s' % (selectedTri, repr(selectedTri.adjTris)))
            for t in selectedTri.adjTris:
                t.highlight2 = not t.highlight2


def main():
    global window, allTriangles, minX, maxX, minY, maxY, r
    if len(sys.argv) < 2:
        print('Usage: %s filename' % sys.argv[0])
        sys.exit(1)

    args = sys.argv[1:]
    while len(args) > 1:
        args = args[1:]

    if not glfw.init():
        print('Error: GLFW failed to initialize')
        sys.exit(1)

    window = glfw.create_window(windowWidth, windowHeight, "Assignment 2", None, None)

    if not window:
        glfw.terminate()
        print('Error: GLFW failed to create a window')
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, keyCallback)
    glfw.set_mouse_button_callback(window, mouseButtonCallback)

    with open(args[0], 'rb') as f:
        allTriangles = readTriangles(f)

    if allTriangles == []:
        return

    minX = min(p[0] for p in allVerts)
    maxX = max(p[0] for p in allVerts)
    minY = min(p[1] for p in allVerts)
    maxY = max(p[1] for p in allVerts)

    if maxX - minX > maxY - minY:
        r *= maxX - minX
    else:
        r *= maxY - minY

    buildTristrips(allTriangles)
    display(wait=True)

    while not glfw.window_should_close(window):
        glfw.wait_events()
        if lastKey == glfw.KEY_ESCAPE:
            sys.exit(0)

    glfw.destroy_window(window)
    glfw.terminate()

def readTriangles(f):
    global allVerts

    errorsFound = False
    lines = f.readlines()

    numVerts = int(lines[0].strip())
    allVerts = [[float(coord) for coord in line.strip().split()] for line in lines[1:numVerts + 1]]

    for i, vert in enumerate(allVerts):
        if len(vert) != 2:
            print(f"Line {i + 2}: vertex does not have two coordinates.")
            errorsFound = True

    numTris = int(lines[numVerts + 1].strip())
    triVerts = [[int(index) for index in line.strip().split()] for line in lines[numVerts + 2:numVerts + 2 + numTris]]

    for i, verts in enumerate(triVerts):
        if len(verts) != 3:
            print(f"Line {i + numVerts + 2}: triangle does not have three vertices.")
            errorsFound = True
        else:
            for v in verts:
                if v < 0 or v >= numVerts:
                    print(f"Line {i + numVerts + 2}: Vertex index is not in range [0, {numVerts - 1}].")
                    errorsFound = True

    tris = []
    for verts in triVerts:
        tris.append(Triangle(verts))

    edges = {}
    for tri in tris:
        for i in range(3):
            v0 = tri.verts[i % 3]
            v1 = tri.verts[(i + 1) % 3]
            edge_key = tuple(sorted((v0, v1)))
            if edge_key in edges:
                adj_tri = edges[edge_key]
                tri.adjTris.append(adj_tri)
                adj_tri.adjTris.append(tri)
            edges[edge_key] = tri

    print(f"Read {numVerts} points and {numTris} triangles")

    return [] if errorsFound else tris
def buildTristrips(triangles):
    count = 0

    def find_adjacent_non_strip_triangles(triangle):
        return [adj for adj in triangle.adjTris if adj.nextTri is None and adj.prevTri is None]

    def start_new_strip(triangle):
        nonlocal count
        count += 1
        triangle.isOnStrip = True
        current_triangle = triangle
        current_triangle.colour = colour.nextColour()

        while True:
            adjacent_non_strip = find_adjacent_non_strip_triangles(current_triangle)

            if not adjacent_non_strip:
                break

            next_triangle = min(adjacent_non_strip, key=lambda t: len(find_adjacent_non_strip_triangles(t)))

            current_triangle.nextTri = next_triangle
            next_triangle.prevTri = current_triangle

            next_triangle.isOnStrip = True
            next_triangle.colour = current_triangle.colour
            current_triangle = next_triangle

    triangles_sorted_by_adjacency = sorted(triangles, key=lambda t: len(find_adjacent_non_strip_triangles(t)))

    for triangle in triangles_sorted_by_adjacency:
        if triangle.nextTri is None and triangle.prevTri is None:
            start_new_strip(triangle)

    print('Generated %d tristrips' % count)
def display(wait=False):
    global lastKey, windowLeft, windowRight, windowBottom, windowTop

    glfw.poll_events()

    glClearColor(1, 1, 1, 0)
    glClear(GL_COLOR_BUFFER_BIT)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if maxX - minX > maxY - minY:
        windowLeft = -0.1 * (maxX - minX) + minX
        windowRight = 1.1 * (maxX - minX) + minX
        windowBottom = windowLeft
        windowTop = windowRight
    else:
        windowTop = -0.1 * (maxY - minY) + minY
        windowBottom = 1.1 * (maxY - minY) + minY
        windowLeft = windowBottom
        windowRight = windowTop

    glOrtho(windowLeft, windowRight, windowBottom, windowTop, 0, 1)

    for tri in allTriangles:
        tri.draw()

    for tri in allTriangles:
        tri.drawPointers()

    glfw.swap_buffers(window)

    if wait:
        sys.stderr.write('Press "p" to proceed ')
        sys.stderr.flush()

        lastKey = None
        while lastKey != 80 and lastKey != glfw.KEY_ESCAPE:
            glfw.wait_events()
            display()

        sys.stderr.write('\r                     \r')
        sys.stderr.flush()

if __name__ == '__main__':
    main()
