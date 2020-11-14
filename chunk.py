# -*- coding: utf-8 -*-
__author__ = 'Michael'

from math import sin
from panda3d.core import *
from array import array
import os.path

CHUNK_SIDE = 32
CHUNK_HEIGHT = 256
CHUNK_SQUARE = CHUNK_SIDE * CHUNK_SIDE
CUBES_PER_CHUNK = CHUNK_HEIGHT * CHUNK_SQUARE
CHUNK_SECTION_HEIGHT = 32

#perlin = PerlinNoise2()
#perlin.setScale(30)


perlin = StackedPerlinNoise2(1000,1000,2,30, 0.1,256,1)


def calcCubeNum(x, y, z):
    return z * CHUNK_SQUARE + y * CHUNK_SIDE + x

class ChunkGeom(object):
    def __init__(self):
        self.triangles = GeomTriangles(Geom.UHStatic)
        self.free = False
        vertexFormat = GeomVertexFormat.getV3n3t2()
        self.vertexData = GeomVertexData('', vertexFormat, Geom.UHStatic)
        self.geom = Geom(self.vertexData)
        self.vertWr = GeomVertexWriter(self.vertexData, 'vertex')
        self.normWr = GeomVertexWriter(self.vertexData, 'normal')
        self.uvWr = GeomVertexWriter(self.vertexData, 'texcoord')

    def getGeom(self):
        return self.geom

    def wrSquareUV(self):
        self.uvWr.addData2f(0,0)
        self.uvWr.addData2f(1,0)
        self.uvWr.addData2f(1,1)
        self.uvWr.addData2f(0,1)

    def wrSquareNorm(self, x, y, z):
        self.normWr.addData3f(x, y, z)
        self.normWr.addData3f(x, y, z)
        self.normWr.addData3f(x, y, z)
        self.normWr.addData3f(x, y, z)

    def addTriangles(self, startVertex):
        self.triangles.addVertices(startVertex, startVertex + 1, startVertex + 2)
        self.triangles.closePrimitive()
        self.triangles.addVertices(startVertex, startVertex + 2, startVertex + 3)
        self.triangles.closePrimitive()

    def addTopSquare(self, cubeX, cubeY, cubeZ):
        startVertex = self.vertWr.getWriteRow()
        self.vertWr.addData3f(cubeX, cubeY, cubeZ + 1)
        self.vertWr.addData3f(cubeX + 1, cubeY, cubeZ + 1)
        self.vertWr.addData3f(cubeX + 1, cubeY + 1, cubeZ + 1)
        self.vertWr.addData3f(cubeX, cubeY + 1, cubeZ + 1)

        self.wrSquareNorm(0,0,1)
        self.wrSquareUV()

        self.addTriangles(startVertex)

    def addBottomSquare(self, cubeX, cubeY, cubeZ):
        startVertex = self.vertWr.getWriteRow()
        self.vertWr.addData3f(cubeX, cubeY + 1, cubeZ)
        self.vertWr.addData3f(cubeX + 1, cubeY + 1, cubeZ)
        self.vertWr.addData3f(cubeX + 1, cubeY, cubeZ)
        self.vertWr.addData3f(cubeX, cubeY, cubeZ)

        self.wrSquareNorm(0,0,-1)
        self.wrSquareUV()
        self.addTriangles(startVertex)

    def addFrontSquare(self, cubeX, cubeY, cubeZ):
        startVertex = self.vertWr.getWriteRow()
        self.vertWr.addData3f(cubeX, cubeY, cubeZ)
        self.vertWr.addData3f(cubeX + 1, cubeY, cubeZ)
        self.vertWr.addData3f(cubeX + 1, cubeY, cubeZ + 1)
        self.vertWr.addData3f(cubeX, cubeY, cubeZ + 1)

        self.wrSquareNorm(0,-1,0)
        self.wrSquareUV()
        self.addTriangles(startVertex)

    def addRearSquare(self, cubeX, cubeY, cubeZ):
        startVertex = self.vertWr.getWriteRow()
        self.vertWr.addData3f(cubeX, cubeY + 1, cubeZ + 1)
        self.vertWr.addData3f(cubeX + 1, cubeY + 1, cubeZ + 1)
        self.vertWr.addData3f(cubeX + 1, cubeY + 1, cubeZ)
        self.vertWr.addData3f(cubeX, cubeY + 1, cubeZ)

        self.wrSquareNorm(0,1,0)
        self.wrSquareUV()
        self.addTriangles(startVertex)

    def addLeftSquare(self, cubeX, cubeY, cubeZ):
        startVertex = self.vertWr.getWriteRow()
        self.vertWr.addData3f(cubeX, cubeY + 1, cubeZ)
        self.vertWr.addData3f(cubeX, cubeY, cubeZ)
        self.vertWr.addData3f(cubeX, cubeY, cubeZ + 1)
        self.vertWr.addData3f(cubeX, cubeY + 1, cubeZ + 1)

        self.wrSquareNorm(-1,0,0)
        self.wrSquareUV()
        self.addTriangles(startVertex)

    def addRightSquare(self, cubeX, cubeY, cubeZ):
        startVertex = self.vertWr.getWriteRow()
        self.vertWr.addData3f(cubeX + 1, cubeY, cubeZ)
        self.vertWr.addData3f(cubeX + 1, cubeY + 1, cubeZ)
        self.vertWr.addData3f(cubeX + 1, cubeY + 1, cubeZ + 1)
        self.vertWr.addData3f(cubeX + 1, cubeY, cubeZ + 1)

        self.wrSquareNorm(1,0,0)
        self.wrSquareUV()
        self.addTriangles(startVertex)

    def addCube(self, cubeX, cubeY, cubeZ):
        self.addTopSquare(cubeX, cubeY, cubeZ)
        self.addBottomSquare(cubeX, cubeY, cubeZ)
        self.addFrontSquare(cubeX, cubeY, cubeZ)
        self.addRearSquare(cubeX, cubeY, cubeZ)
        self.addLeftSquare(cubeX, cubeY, cubeZ)
        self.addRightSquare(cubeX, cubeY, cubeZ)

    def close(self):
        self.geom.addPrimitive(self.triangles)


class Chunk(object):
    def __init__(self, chunkXY):
        self.x, self.y = chunkXY
        self.visible = False
        self.name = "data\%+05dx%+05d"%chunkXY

        if os.path.isfile(self.name):
            print "Read chunk %d, %d"%chunkXY
            self.initArrays(fill=False)
            self.read()
        else:
            print "Generate chunk %d, %d"%chunkXY
            self.initArrays(fill=True)
            self.fillCubes()

        self.createSectionGeomes()

    def initArrays(self, fill):
        if fill:
            self.cubes = array('B',(0 for a in xrange(CUBES_PER_CHUNK)))
            self.faces = array('B',(0 for a in xrange(CUBES_PER_CHUNK)))
        else:
            self.cubes = array('B')
            self.faces = array('B')

    def write(self):
        f = open(self.name,"wb")
        self.cubes.tofile(f)
        self.faces.tofile(f)
        f.close()

    def read(self):
        f = open(self.name,"rb")
        self.cubes.fromfile(f,CUBES_PER_CHUNK)
        self.faces.fromfile(f,CUBES_PER_CHUNK)
        f.close()

    def fillCubes(self):
        #print "Start chunk creation..."
        for x in xrange(CHUNK_SIDE):
            for y in xrange(CHUNK_SIDE):
                ztop = int(perlin.noise(self.x*CHUNK_SIDE+x,self.y*CHUNK_SIDE+y)*50+60)
                #ztop = int(perlin.noise(self.x*CHUNK_SIDE+x,self.y*CHUNK_SIDE+y)*6+40)

                for z in xrange(ztop):
                #for z in xrange(53+((self.x ^ self.y) & 1)):
                #for z in xrange(53):
                    self.addCube(x, y, z)
        #print "chunk created"


    def addCube(self, x, y, z):
        #Отмечаем, с каких сторон нужны грани.
        #Поскольку, если есть соседний куб, то грань всё равно не будет из за него видно.
        #Также говорим соседям, что у них появится сосед, и грань рисовать не нужно

        cubeNum = calcCubeNum(x, y, z)
        faces = 0
        #top - верхняя грань
        #Если не самая верхняя грань (всё равно её не видно)
        #или если куба по соседству нет
        if z != CHUNK_HEIGHT-1  and not\
            self.checkAndUpdateCube(cubeNum + CHUNK_SQUARE, z, CHUNK_SIDE-1, 2):
            #помечаем наличие грани
            faces |= 1

        #bottom - нижняя грань
        #Если не самая нижняя грань (всё равно её не видно)
        #или если куба по соседству нет
        if z != 0 and not\
            self.checkAndUpdateCube(cubeNum - CHUNK_SQUARE, z, 0, 1):
            #помечаем наличие грани
            faces |= 2

        #left - левая грань
        #Если куба по сеседству нет
        if not self.checkAndUpdateCube(cubeNum - 1, x, 0, 8):
            #помечаем наличие грани
            faces |= 4
        #right - правая грань
        #Если куба по сеседству нет
        if not self.checkAndUpdateCube(cubeNum + 1, x, CHUNK_SIDE-1, 4):
            #помечаем наличие грани
            faces |= 8
        #front
        #Если куба по сеседству нет
        if not self.checkAndUpdateCube(cubeNum - CHUNK_SIDE, y, 0, 32):
            #помечаем наличие грани
            faces |= 16
        #rear
        #Если куба по сеседству нет
        if not self.checkAndUpdateCube(cubeNum + CHUNK_SIDE, y, CHUNK_SIDE-1, 16):
            #помечаем наличие грани
            faces |= 32
        self.faces[cubeNum] = faces
        self.cubes[cubeNum] = 1

    def checkAndUpdateCube(self, cubeNum, compareVal, edge, neighborBit):
        """
         Проверяет отстутствие куба по заданным координатам в сhunk.
         Если куб есть, то помечает у него наличие соседа.
         Если координата compareVal находится на границе chunk-а,
         просто считается что куба нет
         neighborBit : наличие соседа с соответствующей стороны
         00000001 (1) top
         00000010 (2) bottom
         00000100 (4) left
         00001000 (8) right
         00010000 (16) front
         00100000 (32) rear
        """
        if compareVal == edge:
            #Крайний куб. Соседа нет
            return False

        else:
            if not self.cubes[cubeNum]:
                #Куба по соседству нет
                return False
            else:
                #Есть куб по соседству.
                #Отметим, что грань теперь не нужна
                self.faces[cubeNum] &= ~neighborBit
                return True

    def addGeomCube(self, chunkGeom, x, y, zInSection, zInChunk):
        cubeNum = calcCubeNum(x, y, zInChunk)
        if not self.cubes[cubeNum]:
            #Куба нет, добавлять нечего
            return

        # "1" - нужна грань (соседа нет)
        faces = self.faces[cubeNum]

        #top
        if faces & 1:
            chunkGeom.addTopSquare(x, y, zInSection)

        #bottom
        if faces & 2:
            chunkGeom.addBottomSquare(x, y, zInSection)

        #left
        if faces & 4:
            chunkGeom.addLeftSquare(x, y, zInSection)

        #right
        if faces & 8:
            chunkGeom.addRightSquare(x, y, zInSection)

        #front
        if faces & 16:
            chunkGeom.addFrontSquare(x, y, zInSection)

        #rear
        if faces & 32:
            chunkGeom.addRearSquare(x, y, zInSection)

    def createSectionGeomes(self):
        self.sectionGeomes = []
        for z in xrange(0, CHUNK_HEIGHT, CHUNK_SECTION_HEIGHT):
            self.sectionGeomes.append(self.createSectionGeom(z,CHUNK_SECTION_HEIGHT))

    def createSectionGeom(self, sectionZ, height):
        sectionGeom = ChunkGeom()
        for zInSection in xrange(height):
            zInGeom = zInSection + sectionZ
            for y in xrange(CHUNK_SIDE):
                for x in xrange(CHUNK_SIDE):
                    self.addGeomCube(sectionGeom, x, y, zInSection, zInGeom)
        sectionGeom.close()
        geom = sectionGeom.getGeom()
        del sectionGeom
        #print "geom created"
        return geom


    def unload(self):
        print "unload %d,%d"%(self.x, self.y)
        self.write()

    def show(self, app):
        if not self.visible:
            self.chunkNode = render.attachNewNode("Chunk %d %d"%(self.x,self.y))
            self.chunkNode.setPos(self.x * CHUNK_SIDE, self.y * CHUNK_SIDE, 0)
            z = 0
            for sectonGeom in self.sectionGeomes:
                node = GeomNode('')
                node.addGeom(sectonGeom)
                nodePath = self.chunkNode.attachNewNode(node)
                nodePath.setTexture(app.texture)
                nodePath.setPos(0, 0, z)
                z+=CHUNK_SECTION_HEIGHT
            self.visible = True
            #print "Chunk %d, %d node attached"%(self.x, self.y)

    def hide(self):
        if self.visible:
            #print "Chunk %d, %d node removed"%(self.x, self.y)
            self.chunkNode.removeNode()
            self.visible = False

    def setFree(self, free):
        self.free = free

    def getFree(self):
        return self.free

