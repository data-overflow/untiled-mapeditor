#========================================
#   MAP EDITOR
#========================================

print('[INFO] Starting map editor...')

from tkinter import *
from tkinter import ttk
import pygame
from pygame.locals import *
from pygame.math import Vector2
import threading
import time
import math
import os


FPS_LIMIT = 144
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BACKGROUND = (10,10,10)

PREVENT_OVERLAP = False

class GameObject:
    def load_image(self, filename):
        self.image = pygame.image.load(filename).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.centre = (self.width/2, self.height/2)

    def set_image(self, imag):
        self.image = imag
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        
    def rect(self):
        """ Generates a rectangle representing the objects location and dimensions """
        return pygame.Rect(self.game.display_surface.blit(self.image, (self.x-self.width/2, self.y-self.height/2)))
                           
    def draw(self):
        """ draw the game object at the current x, y coordinates """
        if not(self.hide):
            self.game.display_surface.blit(self.image, (self.x-self.width/2, self.y-self.height/2))

class Image:
    def __init__(self, loc):
        self.x = 0
        self.y = 0
        self.mapx = 0
        self.mapy = 0
        self.z = False
        self.image = pygame.image.load(loc).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        
    def at(self, x, y):
        self.mapx = x
        self.mapy = y
        return self
    
    def rect(self):    
        return pygame.Rect(self.x-self.width/2, self.y-self.height, self.width, self.height)
    
    def update(self):
        self.game.display_surface.blit(self.image, (self.x-self.width/2, self.y-self.height/2))
        
class Sprite(GameObject):
    '''Create a new Sprite object'''
    def __init__(self, pos=(0,0), z_index=0, map_object=None, x=0, y=0):
        '''Initialise the sprite'''
        self.map = map_object
        self.hide = False
        self.mapx = pos[0]
        self.mapy = pos[1]
        self.x = x
        self.y = y
        self.z_index = 0
        self.brightness = 0 
        self.groups = []
        self.hitbox = (self.x, self.y, 0, 0)
        self.animations = []
        self.animation = {}
        self.frame = 0
        self.playing = False

    def new(self, loc):
        self.load_image(loc)
        return self

    #Position
    def at(self, x, y):
        self.mapx = x
        self.mapy = y
        return self
    
    def goto(self, x, y):
        '''Goto the specified co-ordinates'''
        self.x = x
        self.y = y

    def move(self, x, y):
        '''Move relatively by the specified x, y values'''
        self.x += x
        self.y += y

    def distance_from(self, other):
        '''Get the distance from the other sprite'''
        return (((self.x-other.x)**2)+((self.y-other.y)**2))**(0.5)

    #Groups
    def add_group(self, *args):
        for grp in args:
            self.groups += [grp]

    def remove_group(self, *args):
        for grp in args:
            try:
                self.groups.remove(grp)
            except:
                pass
    
    #Effects
    def show(self):
        self.hide = False
    
    #Collision       
    def collide_rect(self, other):
        '''Check if the sprite's rect collides with the other sprite's rect'''
        if self.rect().colliderect(other.rect()):
            return True
        else:
            return False
        
    def collide_mask(self, other):
        '''Check if the sprite's mask collides with the other sprite's mask. Returns point of collision, else None'''
        offset_x = self.x - other.x
        offset_y = self.y - other.y
        return self.mask.overlap(other.mask, (offset_x, offset_y))

    def collide_hitbox(self, other):
        pygame.Rect(self.hitbox[0], self.hitbox[1], self.hitbox[2], self.hitbox[3]).colliderect(pygame.Rect(other.hitbox[0], other.hitbox[1], other.hitbox[2], other.hitbox[3]))

    #Animation    
    def add_animation(self, name, costumes=[], delay=None, loop=True):
        '''Add a new animation to the sprite'''
        loaded = []
        for loc in costumes:
            img = pygame.image.load(loc).convert_alpha()
            loaded += [pygame.transform.scale2x(img)] #covert alpha
        self.animations += [{'name': name, 'costumes':loaded, 'delay':delay, 'loop':loop, 'frames':len(costumes)}]

    def add_animation_surface(self, name, surfaces=[], delay=None, loop=True):
        self.animations += [{'name': name, 'costumes':surfaces, 'delay':delay, 'loop':loop, 'frames':len(surfaces)}]
        
    def play(self, animation_name):
        '''Play an animation'''
        for anim in self.animations:
            if anim['name'] == animation_name:
                self.animation = anim
                break
        self.frame = 0
        self.set_image(self.animation['costumes'][int(self.frame)])
        self.playing = True

    def stop(self):
        '''Stop playing the running animation'''
        self.playing = False

    def update(self):
        '''Update the object'''
        self.z_index = self.mapy + self.height
        if self.playing:
            if self.animation['delay']!= None:
                self.frame += 1/(FPS_LIMIT*self.animation['delay'])
                if (self.frame >= self.animation['frames']) and self.animation['loop']:
                    if self.animation['loop']:
                        self.frame = 0
                    else:
                        self.frame = self.animation['frames']-1
                        return 0
                self.set_image(self.animation['costumes'][int(self.frame)])
        self.draw()

class Area:
    def __init__(self, shape='rect', centre=(), radius=0, height=0, width=0, points=[]):
        self.shape = shape
        self.centre = centre
        self.radius = radius
        self.points = points
    
    def overlaps(self, other, offset):
        pass

class Map:
    def __init__(self, game, size=(800,600)):
        self.game = game
        self.name = 'untitled'
        self.size = size
        self.camx = 0
        self.camy = 0
        self.color = (50, 130, 0)
        self.objects = []
        self.images_fg = []
        self.images_bg = []
        
    def draw_base(self):
        pygame.draw.rect(self.game.display_surface, self.color, (self.camx, self.camy, self.size[0], self.size[1]))
    
    def design(self, obj=[]):
        self.objects += obj
        for i in obj:
            i.game = self.game

    def decorate(self, obj=[]):
        for i in obj:
            if i.z:
                self.images_fg += [i]
            else:
                self.images_bg += [i]
            i.game = self.game
            
    def update(self):
        self.draw_base()
        for img in self.images_bg:
            img.x = img.mapx + self.camx
            img.y = img.mapy + self.camy
            img.update()
            
        objs = sorted(self.objects, key = lambda i: i.z_index)
        for obj in objs:
            obj.x = obj.mapx + self.camx
            obj.y = obj.mapy + self.camy
            obj.update()

        for img in self.images_fg:
            img.x = img.mapx + self.camx
            img.y = img.mapy + self.camy
            img.update()
        
class Player(Sprite):
    def __init__(self, color=(255,153,153), speed=5):
        super().__init__()
        walk1 = pygame.image.load(r'assets\player\walk1.png').convert_alpha()
        walk2 = pygame.image.load(r'assets\player\walk2.png').convert_alpha()
        walk1_array = pygame.PixelArray(walk1)
        walk2_array = pygame.PixelArray(walk2)
        walk1_array.replace((255,255,255), color)
        walk2_array.replace((255,255,255), color)
        self.add_animation_surface('idle',[walk1])
        self.add_animation_surface('walk',[walk1, walk2], delay = 0.2)        
        self.play('idle')
        self.SPEED = speed*(1/FPS_LIMIT)
        self.color = color

class New1(Sprite): 
    def __init__(self, loc, name):
        super().__init__()
        self.load_image(loc)
        self.name = name

class New2(Image):
    def __init__(self, loc, name, z=False):
        super().__init__(loc)
        self.name = name
        self.z = bool(z)
        
class Editor:
    def __init__(self):
        global SPRITES
        pygame.init()
        pygame.display.set_caption('Map Editor')
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)#, pygame.HWSURFACE| pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        self.blocks = []
        self.font = pygame.font.SysFont("Arial", 18)
        self.running = True
        icon = pygame.image.load('assets/icons/icon128.png')
        pygame.display.set_icon(icon)
        
    def update_fps(self):
        fps = str(int(self.clock.get_fps()))
        fps_text = self.font.render(fps, 1, pygame.Color("white"))
        return fps_text

    def UpdatePlayers(self, data):
        for i in data:
            if i in self.Others.keys():
                self.Others[i].refresh(data[i][0], data[i][1], data[i][2])
            else:
                if i != self.id:
                    self.Others[i] = OtherPlayer(self)
        
    def start(self):
        global csprite, cmap
        undo = []
        cmap = Map(self)
        lastpos = (pygame.mouse.get_pos())    
        while self.running:
            if pygame.mouse.get_pressed()[1]:
                thispos = pygame.mouse.get_pos()
                cmap.camx += thispos[0] - lastpos[0]
                cmap.camy += thispos[1] - lastpos[1] 
                lastpos = pygame.mouse.get_pos()
        
            lastpos = (pygame.mouse.get_pos())
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
            
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                    if event.key == K_1:
                        var.set("Paint")
                        selected_t("Paint")
                    if event.key == K_2:
                        var.set("Erase")
                        selected_t("Erase")
                    if event.key == K_z:
                        try:
                            undo += [cmap.objects.pop()]
                        except:
                            pass
                    if event.key == K_a:            
                        if '1' in str(type(csprite())):
                            cmap.design([csprite().at(lastpos[0]-cmap.camx, lastpos[1]-cmap.camy)])
                        else:
                            cmap.decorate([csprite().at(lastpos[0]-cmap.camx, lastpos[1]-cmap.camy)])

                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not(ERASE):
                            if '1' in str(type(csprite())):
                                cmap.design([csprite().at(event.pos[0]-cmap.camx, event.pos[1]-cmap.camy)])
                            else:
                                cmap.decorate([csprite().at(event.pos[0]-cmap.camx, event.pos[1]-cmap.camy)])
                        else:                            
                            for i in cmap.objects: 
                                if i.rect().collidepoint(event.pos[0], event.pos[1]):
                                    cmap.objects.remove(i)                                    
                                    break
                            for i in cmap.images_fg:
                                if i.rect().collidepoint(event.pos[0], event.pos[1]):
                                    cmap.images_fg.remove(i)                                    
                                    break
                            for i in cmap.images_bg:
                                if i.rect().collidepoint(event.pos[0], event.pos[1]):
                                    cmap.images_bg.remove(i)                                    
                                    break                                                                        

            key = pygame.key.get_pressed()
            if key[K_s]:
                if PREVENT_OVERLAP and cmap.objects and lastpos[0] != cmap.objects[-1].x and lastpos[1] != cmap.objects[-1].y:
                    if '1' in str(type(csprite())):
                        cmap.design([csprite().at(lastpos[0]-cmap.camx, lastpos[1]-cmap.camy)])
                    else:
                        cmap.decorate([csprite().at(lastpos[0]-cmap.camx, lastpos[1]-cmap.camy)])
                else:
                    if '1' in str(type(csprite())):
                        cmap.design([csprite().at(lastpos[0]-cmap.camx, lastpos[1]-cmap.camy)])
                    else:
                        cmap.decorate([csprite().at(lastpos[0]-cmap.camx, lastpos[1]-cmap.camy)])
            
            if key[K_LCTRL] and key[K_z]:
                try:
                    undo += [cmap.objects.pop()]
                except:
                    pass
            
            self.display_surface.fill(BACKGROUND)
            cmap.update()
            hint = csprite().image.copy()
            hint.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
            if not(ERASE):
                self.display_surface.blit(hint, (lastpos[0]-csprite().width/2, lastpos[1]-csprite().height/2))        
            self.display_surface.blit(self.update_fps(), (10,0))
            pygame.display.update()
            self.clock.tick(FPS_LIMIT)
            try:
                root.update()
            except:
                break
            
        pygame.quit()

def build_tree():
    i = 0
    for key in SPRITES:
        tree.insert('', index='end', iid=key, text=key)
        for sub in SPRITES[key]:
            tree.insert(key, index='end', iid=sub, text=sub)
            for s in SPRITES[key][sub]:
                tree.insert(sub, index='end', iid=s, text=s, value="SPRITES['"+key+"']['"+sub+"']['"+s+"']")
                i = i + 1
        
def tree_select(event):    
    global csprite
    value = tree.item(tree.selection()[0], 'value')
    if value:
        csprite = eval(value[0])

def selected_t(value):
    global ERASE
    if value == 'Erase':
        ERASE = True
    else:
        ERASE = False

def selected_b(value):
    global csprite
    csprite = IMAGES_BG[value]

def new_map():
    global cmap
    child = Toplevel(root)
    child.title('Create')
    lb1 = Label(child, text='Name    ', font=('Courier', 14)); en1 = Entry(child, font=('Courier', 12))
    lb2 = Label(child, text='Size    ', font=('Courier', 14)); en2 = Entry(child, font=('Courier', 12))
    lb3 = Label(child, text='Color   ', font=('Courier', 14)); en3 = Entry(child, font=('Courier', 12))
    bt = Button(child, text='CREATE', width=14, font=('Courier', 14), bg='#15F', fg='white', command=lambda: create_new_map(child, en1, en2, en3))
    lb1.grid(row=1, column=1); en1.grid(row=1, column=2)
    lb2.grid(row=2, column=1); en2.grid(row=2, column=2)
    lb3.grid(row=3, column=1); en3.grid(row=3, column=2)
    bt.grid(row=4, column=1, columnspan=2)

def create_new_map(this, en1, en2, en3):
    global cmap
    cmap = Map(main)
    cmap.name = en1.get()
    siz = en2.get().split()
    col = en3.get().split()
    cmap.size = (int(siz[0]), int(siz[1]))
    cmap.color = (int(col[0]), int(col[1]), int(col[2]))
    print('[INFO] New map created')
    this.destroy()

def export_map():
    print('[INFO] Building Map.. ')
    start = time.time()
    name = cmap.name
    code = ''
    code += name + ' = map.new({}, {}, {})\n'.format(str(cmap.size[0]), str(cmap.size[1]), '{'+str(round(cmap.color[0]/255, 4))+', '+str(round(cmap.color[1]/255, 4))+', '+str(round(cmap.color[2]/255, 4))+'}')    
    spawn = ''
    detail = ''
    lines = 0
    size = 0
    clones = {}
    for i in cmap.objects:
        if clones.get(i.name):
            if (i.mapx, i.mapy) in clones[i.name]:
                continue
            else:
                clones[i.name] += [(i.mapx, i.mapy)]
        else:
            clones[i.name] = [(i.mapx, i.mapy)]
    
    for obj in clones:    
        spawn += '{'+obj+'.new,{'
        for pos in clones[obj]:
            spawn += '{'+str(pos[0])+','+str(pos[1])+'},'
        spawn += '}},\n'
        lines += 1

    clones = {}    
    for i in cmap.images_bg+cmap.images_fg:
        if clones.get(i.name):
            if (i.mapx, i.mapy) in clones[i.name]:
                continue
            else:
                clones[i.name] += [(i.mapx, i.mapy, i.z)]
        else:
            clones[i.name] = [(i.mapx, i.mapy, i.z)]
    
    for obj in clones:    
        detail += '{'+obj+'.new,{'
        for pos in clones[obj]:
            if pos[2]:
                detail += '{'+str(pos[0])+','+str(pos[1])+',1},'
            else:
                detail += '{'+str(pos[0])+','+str(pos[1])+'},'
        detail += '}},\n'
        lines += 1               

    if cmap.objects: code += name+':spawn({\n'+spawn+'})\n'
    if cmap.images_bg + cmap.images_bg: code += name+':detail({\n'+detail+'})'
    
    size = len(code)
    print('[INFO] Map built successfully!')
    print('[STATS] Name        : ', name)
    print('[STATS] Lines       : ', lines)
    print('[STATS] Size        : ', size)
    print('[STATS] Build time  : ', round(time.time()-start, 4),'\n')
    print(code)
    return(code)

def build_map(remove_clones=False):
    print('[INFO] Building Map.. ')
    start = time.time()
    name = cmap.name
    code = ''
    code += name + ' = map.new()\n'
    code += name + ':set({}, {}, {})'.format(str(cmap.size[0]), str(cmap.size[1]), '{'+str(cmap.color[0]/255)+', '+str(cmap.color[1]/255)+', '+str(cmap.color[2]/255)+'}') + '\n'
    design = ''
    decorate = ''
    lines = 0
    size = 0
    clones = {}
    for i in cmap.objects:
        if clones.get(i.name):
            if (i.mapx, i.mapy) in clones[i.name]:
                continue
            else:
                clones[i.name] += [(i.mapx, i.mapy)]
        else:
            clones[i.name] = [(i.mapx, i.mapy)]
        design += i.name+'.new():at('+str(i.mapx)+', '+str(i.mapy)+'),\n'
        lines += 1
        
    for i in cmap.images_bg:
        if clones.get(i.name):
            if (i.mapx, i.mapy) in clones[i.name]:
                continue
            else:
                clones[i.name] += [(i.mapx, i.mapy)]
        else:
            clones[i.name] = [(i.mapx, i.mapy)]
        decorate += i.name+'.new():at('+str(i.mapx)+', '+str(i.mapy)+', '+str(bool(i.z)).lower()+'),\n'
        lines += 1

    if cmap.objects: code += name+':design({\n'+design+'})\n'
    if cmap.images_bg + cmap.images_bg: code += name+':decorate({\n'+decorate+'})'
    
    size = len(code)
    print('[INFO] Map built successfully!')
    print('[STATS] Name        : ', name)
    print('[STATS] Lines       : ', lines)
    print('[STATS] Size        : ', size)
    print('[STATS] Build time  : ', round(time.time()-start, 4),'\n')
    print(code)
    return(code)
        
    
NATURE = {
    'Grasses':{
        'HighGrass':lambda: New1('assets/nature/grass1.png', 'highgrass'),
        'LowGrass1':lambda: New1('assets/nature/lowgrass1.png', 'lowgrass1'),
        'LowGrass2':lambda: New1('assets/nature/lowgrass2.png', 'lowgrass2'),
        'MediumGrass1':lambda: New1('assets/nature/mediumgrass1.png', 'mediumgrass1'),
        'MediumBush1':lambda: New1('assets/nature/mediumbush1.png', 'mediumbush1'),
        'TinyGrass':lambda: New2('assets/nature/tinygrass.png', 'tinygrass'),
        'GrassPatch1':lambda: New2('assets/nature/grasspatch1.png', 'grasspatch1'),
        'GrassPatch2':lambda: New2('assets/nature/grasspatch2.png', 'grasspatch2'),
        'GrassPatch3':lambda: New2('assets/nature/grasspatch3.png', 'grasspatch3'),
        'GrassDirt1':lambda: New2('assets/nature/grassdirt1.png', 'grassdirt1')
        },
    'Flowers':{
        'FlowerW':lambda: New1('assets/nature/flowerw.png', 'flowerw'),
        'FlowerR':lambda: New1('assets/nature/flowerr.png', 'flowerr'),
        'FlowerLY':lambda: New1('assets/nature/flowerly.png', 'flowerly'),
        'Player': lambda: New1('assets/player/default1.png', 'player')
        },
    'Stones':{
        'Stone1':lambda: New2('assets/nature/stone1.png', 'stone1'),
        'Stone2':lambda: New2('assets/nature/stone1.png', 'stone2')
        },
    'Trees':{
        'Tree1':lambda: New1('assets/nature/tree1.png', 'tree1'),
        'TreeBranchL':lambda: New2('assets/nature/treebranchl.png', 'treebranchl'),
        'Leaves1':lambda: New2('assets/nature/leaves1.png', 'leaves1', True)
        }
    }

SPRITES = {
    'Nature': NATURE
    }

IMAGES_BG = {
    'TinyGrass':lambda: New2('assets/nature/tinygrass.png', 'tinygrass'),
    'GrassDirt1':lambda: New2('assets/nature/grassdirt1.png', '')
    }

cmap = None
csprite = lambda: New1('assets/player/default1.png', 'player')
ERASE = False

root = Tk()
root.title('Map Editor')
root.iconbitmap('assets/icons/icon128.ico')
root.configure(bg='gray10')
embed = Frame(root, width = WINDOW_WIDTH, height = WINDOW_HEIGHT)
embed.pack(expand=True, fill='both', side='right')
tools = Frame(root, width = 100, height = WINDOW_HEIGHT, bg='gray10')
tools.pack(side='left')
var = StringVar(tools)
var.set("select")

tree=ttk.Treeview(tools, height=20)
tree.bind("<<TreeviewSelect>>", tree_select)
tree.heading('#0', text='Sprite')
build_tree()
tree.grid(row=0, column=1, columnspan=2)

ysb = ttk.Scrollbar(tools, orient='vertical', command=tree.yview)
xsb = ttk.Scrollbar(tools, orient='horizontal', command=tree.xview)

lb1 = Label(tools, text='tool   :', bg='gray10', fg='white', font=('Courier', 12))
option1 = OptionMenu(tools, var, 'Paint','Erase', command=selected_t)
#ttk.Separator(tools, orient=HORIZONTAL).grid(row=0, columnspan=3, sticky="ew")
lb1.grid(row=1, column=1)
option1.grid(row=1, column=2)

lb2 = Label(tools, text='decorate :', bg='gray10', fg='white', font=('Courier', 12))
option2 = OptionMenu(tools, var, *IMAGES_BG.keys(), command=selected_b)
color = Entry(tools)
lb2.grid(row=2, column=1)
option2.grid(row=2, column=2)

build_btn = None
#color.grid(row=2, column=2)
#option1.options(*IMAGES_BG.keys())

menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="New Map", command = new_map)
filemenu.add_command(label="Load Map", state=DISABLED)
filemenu.add_command(label="Save Map", command = export_map)
filemenu.add_command(label="Build Map", command = build_map)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=quit)
menubar.add_cascade(label="File", menu=filemenu)

settingsmenu = Menu(menubar, tearoff=0)
settingsmenu.add_command(label='Clear Screen')
settingsmenu.add_command(label='Toggle Dark Mode')
menubar.add_cascade(label="Options", menu=settingsmenu)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="About")
menubar.add_cascade(label="Help", menu=helpmenu)
root.config(menu=menubar)


os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
os.environ['SDL_VIDEODRIVER'] = 'windib'

print('[INFO] Starting main loop')
main = Editor()
main.start()
