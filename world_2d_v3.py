import pygame 
import random
import math
import socket
import threading

block_w = 5
multiplayer = False
isHost = False

class World:
    def __init__(self, w, h):
        """
        ワールドを初期化します。
        
        Parameters:
            w (int): ワールドの幅
            h (int): ワールドの高さ
        """

        self.blocks = [Air, Stone, Sand, Water, Fire, Wood, Oil, Gunpowder, Fuse, Iron, WoodDust]
        self.width = w
        self.height = h
        self.data = [[Air() for _ in range(self.height)] for _ in range(self.width)]
        self.randamize_color = [[random.randint(0, 30) for _ in range(self.height)] for _ in range(self.width)]
        self.tick_10 = 0

    def in_area(self, x, y):        
        """
        指定されたx, y座標がワールドの範囲内にあるかどうかを返します。
        
        Parameters:
            x (int): x座標
            y (int): y座標
        Returns:
            bool: ワールドの範囲内にあるかどうか
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return True
        return False
    
    def is_can_move(self, x, y, mvx, mvy):
        """
        指定されたx, y座標に mvx, mvy だけ動かす事が出来るかどうかを返します。
        
        Parameters:
            x (int): x座標
            y (int): y座標
            mvx (int): x方向の移動量
            mvy (int): y方向の移動量
        Returns:
            bool: 動かすことが出来るかどうか
        """
        inArea = self.in_area(x, y)
        inArea2 = self.in_area(x+mvx, y+mvy)
        if not inArea or not inArea2:
            return False
        isNotProcessed = self.data[x][y].last_tick != self.tick_10
        isNotProcessed2 = self.data[x+mvx][y+mvy].last_tick != self.tick_10
        mv2p = self.data[x+mvx][y+mvy].move_priority
        myp = self.data[x][y].move_priority
        if inArea and isNotProcessed and isNotProcessed2 and mv2p < myp:
            return True
        return False
    
    def swap_block(self, x1, y1, x2, y2):
        """
        x1, y1とx2, y2のブロックを交換します。
        
        Parameters:
            x1 (int): 交換するブロック1のx座標
            y1 (int): 交換するブロック1のy座標
            x2 (int): 交換するブロック2のx座標
            y2 (int): 交換するブロック2のy座標
        """
        self.data[x1][y1], self.data[x2][y2] = self.data[x2][y2], self.data[x1][y1]
        self.data[x1][y1].last_tick = self.tick_10
        self.data[x2][y2].last_tick = self.tick_10

    def set_block(self, x:int, y:int, id:int ,mode:int = 1) -> None:
        """
        x, y座標にid番目のブロックを配置します。
        modeが1の場合は、既にブロックが存在する場合でも強制的に置き換えます。
        modeが0の場合は、既にブロックが存在する場合は何もしません。
        """
        
        try:
            block = self.blocks[id]
        except:
            block = Air
        block.last_tick = self.tick_10
        if self.in_area(x, y):
            if mode == 1 or self.get_block_id(x, y) == 0:
                self.data[x][y] = block()

    def get_block_id(self, x:int, y:int) -> int:
        """
        x, y座標のブロックのidを取得します。
        
        Parameters:
            x (int): x座標
            y (int): y座標
        Returns:
            int: ブロックのid
        """
        try:
            id = self.blocks.index(self.data[x][y].__class__)
        except:
            id = 0
        return id

    def randamize(self, x, y):
        """
        x, y座標のブロックの色を、乱数に基づいてランダマイズします。
        
        Parameters:
            x (int): x座標
            y (int): y座標
        Returns:
            tuple: (r, g, b)形式の色
        """
        base_color = self.data[x][y].color
        random_color = self.randamize_color[x][y]
        r = base_color[0] - random_color
        g = base_color[1] - random_color
        b = base_color[2] - random_color
        if r < 0:
            r = 0
        if g < 0:
            g = 0
        if b < 0:
            b = 0
        processed_color = (r, g, b)
        return processed_color
    

    def render(self, screen:pygame.Surface, x, y):
        """
        x, y座標のブロックを描画します。

        Parameters:
            screen (pygame.Surface): 描画するSurface
            x (int): x座標
            y (int): y座標
        """
        if not self.data[x][y].invisible:
            pygame.draw.rect(screen, self.randamize(x, y), (x*block_w, y*block_w, block_w, block_w), 0)
    
    def update(self, screen:pygame.Surface):
        """
        全てのブロックを更新し、描画します。

        Parameters:
            screen (pygame.Surface): 描画するSurface
        """
        
        self.tick_10 = (self.tick_10 + 1) % 10
        screen.fill((0, 0, 0))
        for x in range(self.width):
            for y in range(self.height):
                block = self.data[x][y]
                mvx, mvy = block.update()
                isNotAir = not block.__class__ == Air
                block.next_blocks = self.get_next_blocks(x, y)
                if isNotAir:
                    if block.dead:
                        self.set_block(x, y, 0)
                        continue
                    if block.fire:
                        r = random.random()
                        if r < block.fire_chance:
                            self.set_block(x, y, 4)
                        else:
                            self.set_block(x, y, 0)
                    if block.transform is not None:
                        self.set_block(x, y, self.blocks.index(block.transform))
                    if self.in_area(x, y+1):
                        if self.data[x][y+1].move_priority >= block.move_priority:
                            block.isGround = True
                        else:
                            block.isGround = False
                    else:
                        block.isGround = True
                    
                    if self.is_can_move(x, y, mvx, mvy):
                        self.swap_block(x, y, x+mvx, y+mvy)
                        self.render(screen, x+mvx, y+mvy)
                    else:
                        if abs(mvx) > abs(mvy):
                            block.vx *= 0.5
                        else:
                            block.vy *= 0.5
                    self.render(screen, x, y)

    def get_next_blocks(self, x:int, y:int) -> list:
        """
        x, y座標のブロックの隣り合う4ブロックを取得します。
        
        Returns:
            list: [上, 右, 下, 左]の順序で、隣り合うブロックを格納したリスト
        """
        next_blocks = [None, None, None, None]
        x_list = [0, 1, 0, -1]
        y_list = [1, 0, -1, 0]
        for i in range(4):
            if self.in_area(x+x_list[i], y+y_list[i]):
                next_blocks[i] = self.data[x+x_list[i]][y+y_list[i]]
        return next_blocks

    def export_world(self):
        """
        ワールドの状態をエクスポートします。

        Returns:
            list: エクスポートされたワールドの状態
        """
        export_data = self.copy_data(0, 0, self.width, self.height)
        return export_data
    
    def import_world(self, data:list):
        """
        インポートされたワールドの状態を、現在のワールドに適用します。
        
        Parameters:
            data (list): インポートされたワールドの状態
        """
        for x in range(self.width):
            for y in range(self.height):
                self.set_block(x, y, data[x][y])

    def copy_data(self, x:int, y:int, wx:int, wy:int) -> list:
        """
        x, y座標のワールドの状態を、wx, wyの大きさでコピーします。
        
        Parameters:
            x (int): コピーするワールドの左上のx座標
            y (int): コピーするワールドの左上のy座標
            wx (int): コピーするワールドの幅
            wy (int): コピーするワールドの高さ
        Returns:
            list: コピーされたワールドの状態
        """
        data = [[0 for _ in range(wy)] for _ in range(wx)]
        for x2 in range(wx):
            for y2 in range(wy):
                data[x2][y2] = self.get_block_id(x+x2, y+y2)
        return data

    def paste_data(self, x:int, y:int, data:list):
        """
        dataに格納されたワールドの状態を、x, y座標に貼り付けます。
        
        Parameters:
            x (int): 貼り付けるワールドの左上のx座標
            y (int): 貼り付けるワールドの左上のy座標
            data (list): 貼り付けるワールドの状態
        """
        paste_size_x = len(data)
        paste_size_y = len(data[0])
        start_x, start_y = x - paste_size_x//2, y - paste_size_y//2 
        for x2 in range(len(data)):
            for y2 in range(len(data[x2])):
                if data[x2][y2] != 0:
                    self.set_block(start_x+x2, start_y+y2, data[x2][y2])
    
                    
class MultiPlayer(World):
    def __init__(self, w:int, h:int, isHost:bool, port:int, address:str):
        """
        マルチプレイヤーワールドを初期化します。

        Parameters:
            w (int): ワールドの幅
            h (int): ワールドの高さ
            isHost (bool): サーバー役かどうか
            port (int): ポート番号
            address (str): IPアドレス
        """
        super().__init__(w, h)
        self.address = address
        self.port = port
        if isHost:
            self.isHost = True
            self.clients = []
            threading.Thread(target=self.multiplayer_server, daemon=True).start()
        else:
            self.isHost = False
            self.multiplayer_client()
    def update(self, screen:pygame.Surface):
        if self.isHost:
            super().update(screen)
        else:
            screen.fill((0, 0, 0))
            for x in range(self.width):
                for y in range(self.height):
                    block = self.data[x][y]
                    if block.__class__ == Air:
                        continue
                    self.render(screen, x, y)

    def set_block(self, x, y, id, mode = 1, isSelf = True):
        """
        ブロックを設定します。

        Parameters:
            x (int): 設定するブロックのx座標
            y (int): 設定するブロックのy座標
            id (int): 設定するブロックのid
            mode (bool): 上書きするかどうか
            isSelf (bool): 自分自身が行う操作かどうか
        """
        super().set_block(x, y, id, mode)
        if isSelf:
            if self.isHost:
                for client in self.clients:
                    try:
                        client.conn.send(f"set_block,{x},{y},{id},{mode};".encode("utf-8"))
                    except:
                        self.clients.remove(client)
            else:
                self.server.send(f"set_block,{x},{y},{id},{mode};".encode("utf-8"))
    
    def swap_block(self, x1, y1, x2, y2, isSelf = True):
        """
        ブロックを交換します。

        Parameters:
            x1 (int): 交換するブロック1のx座標
            y1 (int): 交換するブロック1のy座標
            x2 (int): 交換するブロック2のx座標
            y2 (int): 交換するブロック2のy座標
            isSelf (bool): 自分自身が行う操作かどうか
        """
        super().swap_block(x1, y1, x2, y2)
        if isSelf:
            if self.isHost:
                for client in self.clients:
                    try:
                        client.conn.send(f"swap_block,{x1},{y1},{x2},{y2};".encode("utf-8"))
                    except:
                        self.clients.remove(client)
            else:
                self.server.send(f"swap_block,{x1},{y1},{x2},{y2};".encode("utf-8"))
    
    def multiplayer_server(self):
        """
        マルチプレイヤーサーバーを開始し、クライアントからの接続を待機します。
        接続が確立されると、新しいConnectionオブジェクトを作成し、
        クライアントリストに追加します。
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.address, self.port))
        sock.listen(5)
        while True:
            conn, addr = sock.accept()
            self.clients.append(Connection(conn, addr, self, True))
            send_data = [0 for _ in range(self.width * self.height)]
            i = 0
            for x in range(self.width):
                for y in range(self.height):
                    send_data[i] = self.get_block_id(x, y)
                    i += 1
            conn.send(f"sync_world,{','.join(map(str, send_data))};".encode("utf-8"))
            
    def sync_world(self, data):
        """
        サーバーから送られてきたワールドデータを受け取り、
        ワールドデータを更新します。
        """
        i = 0
        for x in range(self.width):
            for y in range(self.height):
                self.set_block(x, y, data[i], 1, False)
                i += 1


    def multiplayer_client(self):
        """
        マルチプレイヤークライアントを開始し、サーバーとの接続を確立します。
        サーバーとの接続が確立されると、新しいConnectionオブジェクトを作成し
        そのオブジェクトをconnectionに格納します。
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.address, self.port))
        self.connection = Connection(self.server, self.address, self, False)


class Connection:
    def __init__(self, conn:socket, addr:str, world:MultiPlayer, isHostSide:bool = False):
        """
        Connectionオブジェクトを初期化します.

        Parameters:
            conn (socket): サーバーとクライアントの間でデータをやり取りするためのソケット
            addr (str): クライアントのIPアドレス
            world (MultiPlayer): マルチプレイヤーワールド
            isHost (bool): サーバー役かどうか
        """
        self.conn = conn
        self.addr = addr
        self.world = world
        self.isHostSide = isHostSide
        threading.Thread(target=self.recv_loop, daemon=True).start()

    def recv_loop(self):
        """
        クライアント・サーバーから送られてきたコマンドを処理します.

        1024バイトずつ受信し、";"で区切られたコマンドを処理します。
        例えば、"set_block,1,2,3;"というコマンドがあった場合、
        "set_block"というコマンドに[1,2,3]という引数を渡します。
        また、ホスト役の場合は、全てのクライアントに同じコマンドを送信します。
        """
        buffer = ""
        raw_command = ""
        loop = True
        while loop:
            try:
                data = self.conn.recv(1024)
            except:
                loop = False
                self.conn.close()
                self.world.clients.remove(self)
            decoded = data.decode("utf-8")
            if not data:
                loop = False
                self.conn.close()
                self.world.clients.remove(self)
                break

            if self.isHostSide:
                for client in self.world.clients:
                    if client.addr != self.addr:
                        client.conn.send(data)

            buffer += decoded
            while True:
                if ";" in buffer:
                    i = buffer.find(";")
                    raw_command = buffer[:i]
                    buffer = buffer[i+1:]
                    try:
                        command = raw_command.split(",")
                        args = [int(i) for i in command[1:]]
                        self.do_command(command[0], args)
                    except:
                        print("Error in command")
                        print(raw_command)
                else:
                    break
    
    def do_command(self, command:str, args:list):
        """
        指定されたコマンドを実行します.

        Parameters:
            command (str): 実行するコマンド
            args (list): コマンドに渡す引数
        """
        if command == "set_block":
            self.world.set_block(args[0], args[1], args[2], args[3], False)
        elif command =="swap_block":
            self.world.swap_block(args[0], args[1], args[2], args[3], False)
        elif command =="sync_world":
            self.world.sync_world(args)
                

class Block:
    def __init__(self):
        self.vx = 0
        self.vy = 0
        self.dead = False
        self.can_burn = False
        self.burn_level = 0
        self.burn_threshold = 10
        self.fire = False
        self.fire_chance = 0.0
        self.speed_decay = 0.99
        self.gravity = 1
        self.color = (0, 0, 0)
        self.invisible = False
        self.move_priority = 100
        self.last_tick = 0
        self.isGround = False
        self.next_blocks = [None, None, None, None] #up, right, down, left
        self.can_electric = False
        self.electric_level = 0
        self.durability = 10000
        self.transform = None
        self.transform_to = None
    def update(self):
        return 0, 0
    
    def impact(self, count, x, y, direction_from):
        if count <= 0:
            return
        for i in range(4):
            if i == direction_from:
                continue
            if self.next_blocks[i] is not None:
                self.next_blocks[i].impact(count-1, x, y, direction_from)
        self.vx, self.vy = x, y
        self.durability -= math.sqrt(self.vx**2 + self.vy**2)
        if self.durability <= 0 and self.transform_to is not None:
            self.transform = self.transform_to
        
    def electric(self, level):
        if level <= 0 or self.can_electric == False or self.electric_level >= level:
            return
        if self.electric_level < level:
            self.electric_level = level
        for i in range(4):
            if self.next_blocks[i] is not None:
                self.next_blocks[i].electric(level-1)
    

class Stone(Block):
    def __init__(self):
        super().__init__()
        self.color = (100, 100, 100)
        self.transform_to = Sand
        self.durability = 200

    def impact(self, count, x, y, direction_from):
        return super().impact(count, x, y, direction_from)


class Air(Block):
    def __init__(self):
        super().__init__()
        self.invisible = True
        self.color = (255, 255, 255)
        self.move_priority = 0


class Sand(Block):
    def __init__(self):
        super().__init__()
        self.color = (220, 200, 170)
        self.move_priority = 3
    
    def update(self):
        self.vx *= self.speed_decay
        self.vy *= self.speed_decay
        mvx, mvy = self.vx, self.vy + self.gravity
        if self.isGround:
            if self.next_blocks[1] is not None and self.next_blocks[1].move_priority < self.move_priority:
                mvx += 1
            elif self.next_blocks[3] is not None and self.next_blocks[3].move_priority < self.move_priority:
                mvx -= 1
        return int(mvx), int(mvy)


class Water(Block):
    def __init__(self):
        super().__init__()
        self.color = (0, 0, 255)
        self.move_priority = 2

    def update(self):
        self.vx *= self.speed_decay
        self.vy *= self.speed_decay
        mvx, mvy = self.vx, self.vy
        if self.isGround:
            if random.random() < 0.5:
                mvx += -1
            else:
                mvx += 1
        else:
            mvy += self.gravity
        return int(mvx), int(mvy)


class Fire(Block):
    def __init__(self):
        super().__init__()
        self.lifetime = 120
        self.color = (255, 0, 0)
        self.move_priority = 1

    def update(self):
        self.vx *= self.speed_decay
        self.vy *= self.speed_decay
        mvx, mvy = self.vx, self.vy
        self.lifetime -= 1
        for i in range(4):
            block = self.next_blocks[i]
            if block is not None and block.can_burn:
                block.burn_level += 1
                
        r = random.random()
        if r < 0.4:
            mvy -= 1
        elif r < 0.7:
            mvx += 1
        elif r < 0.98:
            mvx -= 1
        else:
            self.dead = True
        if self.lifetime <= 0:
            self.dead = True
        return int(mvx), int(mvy)
    

class Wood(Block):
    def __init__(self):
        super().__init__()
        self.color = (150, 75, 0)
        self.can_burn = True
        self.burn_threshold = 10
        self.fire_chance = 0.4
        self.durability = 10
        self.transform_to = WoodDust
    
    def update(self):
        if self.burn_level >= self.burn_threshold:
            self.fire = True
        return 0, 0
    
    def impact(self, count, x, y, direction_from):
        return super().impact(count, x, y, direction_from)
    

class WoodDust(Sand):
    def __init__(self):
        super().__init__()
        self.color = (200, 125, 0)
        self.can_burn = True
        self.burn_threshold = 3
        self.fire_chance = 0.6
    
    def update(self):
        mvx, mvy = super().update()
        if self.burn_level >= self.burn_threshold:
            self.fire = True
        return mvx, mvy


class Oil(Water):
    def __init__(self):
        super().__init__()
        self.move_priority = 1.5
        self.color = (200, 200, 0)
        self.can_burn = True
        self.burn_threshold = 5
        self.fire_chance = 1.0

    def update(self):
        mvx, mvy = super().update()
        if self.burn_level >= self.burn_threshold:
            self.fire = True
        return mvx, mvy


class Gunpowder(Sand):
    def __init__(self):
        super().__init__()
        self.color = (200, 200, 200)
        self.can_burn = True
        self.burn_threshold = 1
        self.fire_chance = 1
    
    def update(self):
        mvx, mvy = super().update()
        if self.burn_level >= self.burn_threshold:
            xlist = [0, 1, 0, -1]
            ylist = [1, 0, -1, 0]
            power = 5
            for i in range(4):
                if self.next_blocks[i] is not None:
                    self.next_blocks[i].impact(4, xlist[i]*power, ylist[i]*power, (i+2)%4)
            self.fire = True
        return mvx, mvy

class Fuse(Wood):
    def __init__(self):
        super().__init__()
        self.color = (200, 50, 0)
        self.burn_threshold = 1
        self.fire_chance = 1.0
        self.transform_to = None

class Iron(Block):
    def __init__(self):
        super().__init__()
        self.color = (150, 150, 150)
        self.transform_to = None


pygame.init()
pygame.display.set_mode((800, 500))
world_data = World(160, 100)

def pygame_input(out:str, error:str = ""):
    clock = pygame.time.Clock()
    input_screen = pygame.display.get_surface()
    input_text = ""
    while True:
        input_screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 30)
        text = font.render(f"{out}{input_text}", True, (255, 255, 255))
        error_text = font.render(error, True, (255, 0, 0))
        input_screen.blit(text, (30, 10))
        input_screen.blit(error_text, (30, 40))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    name = pygame.key.name(event.key)
                    if len(name) == 1:
                        input_text += name
        clock.tick(60)



def main():
    global world_data, multiplayer, isHost
    screen = pygame.display.get_surface()
    runnning = True
    clock = pygame.time.Clock()
    mouse_event = None
    mouse_button_holding = [False, False]
    place_size = 1
    blocks = world_data.blocks
    sel = 0
    clipboard = []
    temp_save = []
    mode = "normal" #normal, copy, paste
    copy_x, copy_y = 0, 0
    while runnning:
        world_data.update(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if multiplayer:
                    if isHost:
                        for client in world_data.clients:
                            client.conn.close()
                    else:
                        world_data.server.close()
                runnning = False
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_event = event
                    if event.button == 1:
                        mouse_button_holding[0] = True
                    elif event.button == 3:
                        mouse_button_holding[1] = True
                    if event.button == 2:
                        x, y = event.pos[0] // block_w, event.pos[1] // block_w
                        block = world_data.data[x][y].__class__
                        if block in blocks:
                            for i in range(len(blocks)):
                                if blocks[i] == block:
                                    sel = i
                                    break
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        mouse_button_holding[0] = False
                    elif event.button == 3:
                        mouse_button_holding[1] = False
                if event.type == pygame.MOUSEMOTION:
                    mouse_event = event
                if event.type == pygame.MOUSEWHEEL:
                    next_size = place_size + event.y
                    if next_size > 0:
                        place_size = next_size
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        sel = 1
                    if event.key == pygame.K_2:
                        sel = 2
                    if event.key == pygame.K_3:
                        sel = 3
                    if event.key == pygame.K_4:
                        sel = 4
                    if event.key == pygame.K_5:
                        sel = 5
                    if event.key == pygame.K_6:
                        sel = 6
                    if event.key == pygame.K_7:
                        sel = 7
                    if event.key == pygame.K_a:
                        next_sel = sel - 1
                        if next_sel >= 0:
                            sel = next_sel
                    if event.key == pygame.K_d:
                        next_sel = sel + 1
                        if next_sel < len(blocks):
                            sel = next_sel
                    if event.key == pygame.K_r:
                        for x in range(world_data.width):
                            for y in range(world_data.height):
                                world_data.set_block(x, y, 0)
                    if event.key == pygame.K_w:
                        place_size += 1
                    if event.key == pygame.K_s and place_size > 1:
                        place_size -= 1
                    if event.key == pygame.K_o:
                        temp_save = world_data.export_world()
                    if event.key == pygame.K_p:
                        world_data.import_world(temp_save)
                    if event.key == pygame.K_m and multiplayer == False:
                        out = "Are you host? (yes/no/cancel): "
                        error = ""
                        while True:
                            msg = pygame_input(out, error)
                            if msg == "yes":
                                isHost = True
                                multiplayer = True
                                break
                            elif msg == "no":
                                multiplayer = True
                                break
                            elif msg == "cancel":
                                break
                            else:
                                error = "Invalid input"
                        if isHost:
                            error = ""
                            while True:
                                port = pygame_input("Port: ", error)
                                if port == "cancel":
                                    break
                                try:
                                    world_data = MultiPlayer(160, 100, True, int(port), "")
                                    break
                                except Exception as e:
                                    print(e)
                                    error = "Invalid input"
                        else:
                            error = ""
                            while True:
                                ip = pygame_input("IP: ", error)
                                if ip == "cancel":
                                    break
                                port = pygame_input("Port: ", error)
                                if port == "cancel":
                                    break
                                try:
                                    world_data = MultiPlayer(160, 100, False, int(port), ip)
                                    break
                                except:
                                    error = "Invalid input"
                                

                    if mouse_event != None:
                        if event.key == pygame.K_c:
                            x, y = int(mouse_event.pos[0]//block_w), int(mouse_event.pos[1]//block_w)
                            if mode == "copy":
                                x1, y1 = max(copy_x, x), max(copy_y, y)
                                x2, y2 = min(copy_x, x), min(copy_y, y)
                                wx, wy = x1 - x2, y1 - y2
                                clipboard = world_data.copy_data(x2, y2, wx, wy)
                                mode = "normal"
                            elif mode == "normal":
                                mode = "copy"
                                copy_x, copy_y = x, y
                        if event.key == pygame.K_v:
                            if mode == "paste":
                                world_data.paste_data(x, y, clipboard)
                                mode = "normal"
                            elif mode == "normal":
                                mode = "paste"
        if mouse_event != None:
            x, y = int(mouse_event.pos[0]//block_w), int(mouse_event.pos[1]//block_w)
            if mouse_button_holding[0]:
                for i in range(place_size):
                    for j in range(place_size):
                        place_x = x - place_size//2 + i
                        place_y = y - place_size//2 + j
                        world_data.set_block(place_x, place_y, sel, 0)
            if mouse_button_holding[1]:
                for i in range(place_size):
                    for j in range(place_size):
                        place_x = x - place_size//2 + i
                        place_y = y - place_size//2 + j
                        world_data.set_block(place_x, place_y, 0)
            if mode == "paste":
                paste_size_x = len(clipboard)
                paste_size_y = len(clipboard[0])
                pygame.draw.rect(screen, (0, 0, 255), ((x - paste_size_x//2)*block_w, (y - paste_size_y//2)*block_w, block_w*paste_size_x, block_w*paste_size_y), 1)
            elif mode == "copy":
                x1, y1 = max(copy_x, x), max(copy_y, y)
                x2, y2 = min(copy_x, x), min(copy_y, y)
                wx, wy = x1 - x2, y1 - y2
                pygame.draw.rect(screen, (0, 255, 0), (x2*block_w, y2*block_w, block_w*wx, block_w*wy), 1)
            elif mode == "normal":
                pygame.draw.rect(screen, (255, 0, 0), ((x - place_size//2)*block_w, (y - place_size//2)*block_w, block_w*place_size, block_w*place_size), 1)
        
        for i, block in enumerate(blocks):
            if i == sel:
                stroke = 1
            else:
                stroke = 0
            pygame.draw.rect(screen, block().color, (blocks.index(block)*60, 10, 60, 20), stroke)

            font = pygame.font.SysFont(None, 15)
            text = font.render(block.__name__, True, (255, 255, 255))
            screen.blit(text, (blocks.index(block)*60, 15))
        pygame.display.update()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__": 
    main()
        