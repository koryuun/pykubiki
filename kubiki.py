# -*- coding: utf-8 -*-
__author__ = 'Michael'

from math import pi, sin, cos, sqrt, radians, floor
from itertools import product, chain
from collections import OrderedDict

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import *

from chunk import *


class KubikiApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.viewDistanceChunks = 4
        self.viewDistance = (self.viewDistanceChunks+0.5)*CHUNK_SIDE


        self.visibleChunksXY = set()
        self.visibleChunks = {}
        self.chunksForLoader = {}


        # Disable the camera trackball controls.
        self.disableMouse()

        self.camAngleA = 0
        self.camAngleB = 0

        self.currChunkXY = (None, None)
        self.currChunk = None

        self.accept('arrow_left', self.evtArrowLeft)
        self.accept('arrow_left-repeat', self.evtArrowLeft)
        self.accept('arrow_right', self.evtArrowRight)
        self.accept('arrow_right-repeat', self.evtArrowRight)
        self.accept('arrow_up', self.evtArrowUp)
        self.accept('arrow_up-repeat', self.evtArrowUp)
        self.accept('arrow_down', self.evtArrowDown)
        self.accept('arrow_down-repeat', self.evtArrowDown)
        self.accept('w', self.evtForward)
        self.accept('w-repeat', self.evtForward)
        self.accept('s', self.evtBack)
        self.accept('s-repeat', self.evtBack)
        self.accept('i',self.render.analyze)

        self.texture = self.loader.loadTexture("dirt.png")
        self.texture.setMagfilter(Texture.FTNearest)
        self.texture.setMinfilter(Texture.FTLinearMipmapLinear)

        self.xyzInfo = OnscreenText(text="text", align=TextNode.ALeft, parent=pixel2d, fg = (1,1,1,1), bg = (0,0,0,0.7))
        self.xyzInfo.setScale(18, 20)
        self.xyzInfo.setPos(5, -20)

        #self.messenger.toggleVerbose()

        self.setFrameRateMeter(True)
        #self.chunkLoaderThread = threading.Thread(target=chunkLoader)
        #self.chunkLoaderThread.start()


        taskMgr.doMethodLater(0.01, self.refreshChunksTask, 'refreshChunksTask')
        taskMgr.setupTaskChain('chunkLoaderTaskChain', numThreads = 1)

        bgColor = (0.3, 0.5, 1)
        self.setBackgroundColor(*bgColor)
        self.initFog(bgColor)
        self.camLens.setFar(self.viewDistance)

        self.setCamPos(CHUNK_SIDE/2,CHUNK_SIDE/2,32)

        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.8, 0.8, 0.5, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(-30, -60, 0)
        render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)


    def initFog(self, color):
        self.fog = Fog("fog")
        self.fog.setColor(*color)
        self.fog.setLinearRange(self.viewDistance*0.8,self.viewDistance)
        self.render.setFog(self.fog)

    @staticmethod
    def coordConvert(angA, angB, l):
        #Преобразование из системы коородинат Panda3d в координаты для формулы
        angA = radians(90 + angA)
        angB = radians(90 - angB)
        x = sin(angB) * cos(angA) * l
        y = sin(angB) * sin(angA) * l
        z = cos(angB) * l
        return x, y, z

    #----------Events--------------
    def evtArrowLeft(self):
        self.camAngleA+=1

        if self.camAngleA>180:
            self.camAngleA = -179

        self.camera.setH(self.camAngleA)

    def evtArrowRight(self):
        self.camAngleA-=1

        if self.camAngleA<-179:
            self.camAngleA = 180

        self.camera.setH(self.camAngleA)

    def evtArrowUp(self):
        self.camAngleB += 1

        if self.camAngleB > 90:
            self.camAngleB = 90

        self.camera.setP(self.camAngleB)

    def evtArrowDown(self):
        self.camAngleB -= 1

        if self.camAngleB < -90:
            self.camAngleB = -90

        self.camera.setP(self.camAngleB)


    def evtForward(self):
        dx, dy, dz = self.coordConvert(self.camAngleA, self.camAngleB,0.2)
        x, y, z = self.camera.getPos()
        self.setCamPos(x+dx, y+dy, z+dz)

    def evtBack(self):
        dx, dy, dz = self.coordConvert(self.camAngleA, self.camAngleB,-0.2)
        x, y, z = self.camera.getPos()
        self.setCamPos(x+dx, y+dy, z+dz)

    #------------------------------
    def setCamPos(self, x, y, z):
        self.camera.setPos(x, y, z)

        chunkXY = (int(floor(x/CHUNK_SIDE)), int(floor(y/CHUNK_SIDE)))
        if chunkXY != self.currChunkXY:
            self.setCurrChunk(chunkXY)

        self.xyzInfo.setText("x=%2.2f\ny=%2.2f\nz=%2.2f"%(x,y,z))

    def setCurrChunk(self, chunkXY):
        print chunkXY
        self.currChunkXY = chunkXY
        self.updateVisibleChunkSet()


    @staticmethod
    def loadChunk(chunkXY):
        return Chunk(chunkXY)


    def createVisibleChunkList(self):

        currChunkX, currChunkY = self.currChunkXY


        #Создаём список смещений чанков от текущего, и фильтруем его через функцию чтобы скруглить
        #слишком удалённые углы
        viewDistSquare = (self.viewDistanceChunks + 1)**2
        #chunkList = filter( lambda xy : xy[0]**2 + xy[1]**2 <=  viewDistSquare,
        #                    product(xrange(-self.viewDistanceChunks, self.viewDistanceChunks + 1),
        #                            xrange(-self.viewDistanceChunks, self.viewDistanceChunks + 1)))
        chunkList = product(xrange(-self.viewDistanceChunks, self.viewDistanceChunks + 1),
                                    xrange(-self.viewDistanceChunks, self.viewDistanceChunks + 1))

        def maxXY(xy1,xy2):
            x1, y1 = xy1
            x2, y2 = xy2
            max1 = max(abs(x1),abs(y1))
            max2 = max(abs(x2),abs(y2))
            return cmp(max1, max2)

        chunkList = [ (x + currChunkX, y + currChunkY) for x,y in sorted(chunkList, maxXY)]

        return chunkList

    def updateVisibleChunkSet(self):
        #Новый массив с видимыми чанками
        self.visibleChunksXY = self.createVisibleChunkList()
        self.chunkRefreshNeeded = True


    def refreshChunksTask(self, task):
        if not self.chunkRefreshNeeded:
            return task.again

        if taskMgr.hasTaskNamed('chunkLoaderTask'):
            return task.again



        self.chunkRefreshNeeded = False

        print "thinking..."

        chunksToUnload = {}
        oldVisibleChunks = self.visibleChunks
        self.visibleChunks = {}

        #Старые видимые чанки переносим в новые или готовим к выгрузке
        for xy, chunk in oldVisibleChunks.iteritems():
            if isinstance(chunk,Chunk):
                if xy in self.visibleChunksXY:
                    self.visibleChunks[xy] = chunk
                else:
                    chunksToUnload[xy] = chunk
                    chunk.hide()
                    chunk.setFree(True)

        chunksToLoadXY = set()



        #Недостающие чанки получаем из загруженных или готовим задание на загрузку
        for xy in self.visibleChunksXY:
            if not self.visibleChunks.has_key(xy):
                chunk = self.chunksForLoader.get(xy, None)
                if isinstance(chunk,Chunk):
                    chunk.show(self)
                    self.visibleChunks[xy] = chunk
                    del self.chunksForLoader[xy]
                else:
                    if len(chunksToLoadXY)<=2:
                        chunksToLoadXY.add(xy)



        #Загруженные, но ненужные чанки - на выгрузку

        for xy, chunk in self.chunksForLoader.iteritems():
            chunk.setFree(True)


        #Задание на выгрузку
        for xy, chunk in chunksToUnload.iteritems():
            self.chunksForLoader[xy] = chunk


        #Задание на загрузку
        for xy in chunksToLoadXY:

            self.chunksForLoader[xy] = True


        #Запускаем задачу загрузки-выгрузки
        taskMgr.add(self.chunkLoaderTask, 'chunkLoaderTask',
                    taskChain = 'chunkLoaderTaskChain')

        print "end of thinking"

        return task.again


    def chunkLoaderTask(self, task):
        """
        Запускается при необходимости загрузить-выгрузить чанки.
        Выполняется в отдельном потоке
        """
        print "loader Task"

        for xy, chunk in self.chunksForLoader.items():
            if chunk == True:
                #Грузим новый чанк
                newChunk = Chunk(xy)
                self.chunksForLoader[xy] = newChunk
                self.chunkRefreshNeeded = True
            elif isinstance(chunk, Chunk) and chunk.getFree():
                #Выгружаем ненужный чанк
                chunk.unload()
                del self.chunksForLoader[xy]
            else:
                print "chunkLoaderTask:unexpected chunk"

        print "loader Task end"
        return Task.done



app = KubikiApp()
app.run()
