import asyncio
import vec
import time
import random
import player
import level
import util
import pdb
import math

JUMP_AUDIO = 1
HIT_GROUND_AUDIO = 2
HIT_PLAYER_AUDIO = 3
THROW_AUDIO = 4
DEATH_AUDIO = 5

MAX_THROWING_FORCE = 30
SNOWBALL_SPAWN_DISTANCE = 30;
SNOWBALL_SIZE = 10
SNOWBALL_DAMAGE = 0.5

RUN_ACCELERATION = 1.0
GRAVITY_ACCELERATION = 1.3
PLAYER_MAX_SPEED = 10

def run_main_loop(lobby, stop_event, event_loop):
    for client in lobby.clients.values():
        while True:
            rx = random.randint(0, 
                                len(level.tiles[0])*level.TILE_SIZE)
            ry = random.randint(0, 
                                len(level.tiles)*level.TILE_SIZE)
            _, can_place = level.can_move_to(level.PLAYER_WIDTH,
                                      level.PLAYER_HEIGHT,
                                      rx, ry)
            if can_place:
                client.player.position = (rx, ry)
                break

    running = True
    while not stop_event.is_set():
        update_players(lobby.clients)
        changed_healths, destroyed_snowballs, player_hit,\
                ground_hit = update_snowballs(lobby)

        if changed_healths:
            asyncio.run_coroutine_threadsafe(
                broadcast_health(
                    lobby.clients,
                    changed_healths), event_loop)

            for player in changed_healths:
                if player.health == 0:
                    player.position = -1000, -1000

        if destroyed_snowballs:
            asyncio.run_coroutine_threadsafe(
                broadcast_deleted_snowballs(
                    lobby.clients,
                    destroyed_snowballs), event_loop)

        if lobby.has_snowballs():
            asyncio.run_coroutine_threadsafe(
                broadcast_snowballs(lobby), event_loop)


        if player_hit:
            asyncio.run_coroutine_threadsafe(
                broadcast_audio(lobby.clients,
                                HIT_PLAYER_AUDIO),
                event_loop)

        elif ground_hit:
            asyncio.run_coroutine_threadsafe(
                broadcast_audio(lobby.clients,
                                HIT_GROUND_AUDIO),
                event_loop)

        asyncio.run_coroutine_threadsafe(broadcast_positions(lobby.clients), event_loop)
        time.sleep(1/30)


async def broadcast_deleted_snowballs(clients, deleted_snowballs):
    for ball_id in deleted_snowballs:
        await util.broadcast(clients, 
                             'delete ball:' + str(ball_id))

async def broadcast_positions(clients):
    for username in clients:
        x, y = clients[username].player.position
        await util.broadcast(clients,
            'position:{} {} {}'.format(username, x, y))


async def broadcast_snowballs(lobby):
    message = 'snowballs:'
    # if not lobby.snowballs.values():
    #     message += ' '
    for snowball in lobby.snowballs.values():
        x, y = snowball.position
        message += '{} {} {};'.format(snowball.id, x, y)
    await util.broadcast(lobby.clients, message)
    

async def broadcast_health(lobby, changed_healths):
    message = 'health:'
    for player in changed_healths:
        await util.broadcast(lobby, 
                             message + 
                             player.name + ' ' + 
                             str(player.health))


async def broadcast_audio(clients, audio):
    for username in clients:
        await util.broadcast(clients, "play:" + str(audio))


async def send_audio_to_user(client, audio):
    await util.send_message(client, "play:" + str(audio))


async def play_throw_sound(lobby):
    await broadcast_audio(lobby.clients, THROW_AUDIO)


async def jump(client):
    vx, vy = client.player.velocity
    if client.player.on_ground:
        client.player.velocity = vx, vy - 20
        await send_audio_to_user(client, JUMP_AUDIO)


def other_players(player, clients):
    return {p: v for p, v in clients.items() if p != player.name}

def all_players(clients):
    return {p: v.player for p, v in clients.items()}


def update_snowballs(lobby):
    changed_healths = []
    destroyed_snowballs = []
    player_hit = False
    ground_hit = False
    for id, snowball in lobby.snowballs.items():
        new_vel = vec.add(snowball.velocity, 
                          (0, GRAVITY_ACCELERATION))

        new_pos = vec.add(snowball.position, new_vel)
        new_x, new_y = new_pos
        hit_object, can_move = level.can_move_to(SNOWBALL_SIZE,
                                       SNOWBALL_SIZE,
                                      round(new_x), round(new_y),
                                      all_players(lobby.clients))
        if can_move:
            snowball.velocity = new_vel
            snowball.position = new_pos
        else:
            destroyed_snowballs.append(id)
            if isinstance(hit_object, player.Player):
                player_hit = True
                speed = vec.length(snowball.velocity)
                hit_object.health = max(0, hit_object.health - 
                                    speed*SNOWBALL_DAMAGE)
                changed_healths.append(hit_object)
            else:
                ground_hit = True
    lobby.snowballs = {id: v 
                       for id, v in lobby.snowballs.items()
                      if id not in destroyed_snowballs}
    return changed_healths, destroyed_snowballs, player_hit, ground_hit


def update_player(player, clients):
    # pdb.set_trace()
    px, py = player.position
    vx, vy = player.velocity
    hit_object, can_move = level.can_move_to(
        level.PLAYER_WIDTH, 
        level.PLAYER_HEIGHT,
        px,
        round(py + vy))

    if can_move:
        player.velocity = (vx, vy + GRAVITY_ACCELERATION)
        player.position = (px, round(py + vy))
        if py != player.position[1]:
            player.on_ground = False
    else:
        if vy > 0 and isinstance(hit_object, tuple) and len(hit_object) == 2:
            player.position = (px, hit_object[1] - level.PLAYER_HEIGHT)
        player.velocity = (vx, 0)
        player.on_ground = True

    px, py = player.position
    vx, vy = player.velocity
    _, can_move = level.can_move_to(level.PLAYER_WIDTH,
                                    level.PLAYER_HEIGHT - 1,
                                    round(px + vx), py)
    if can_move:
        dx = (player.left_pressed*(-1) + player.right_pressed)
        new_vx = vx * 0.9 + dx
        if new_vx > PLAYER_MAX_SPEED:
            new_vx = PLAYER_MAX_SPEED * new_vx / new_vx
        player.velocity = (new_vx, vy)
        player.position = (round(px + vx), py)
    else:
        player.velocity = (0, vy)


def update_players(clients):
    for client_name in clients:
        player = clients[client_name].player
        update_player(player, clients)


def create_snowball_id(lobby):
    if not lobby.snowballs:
        return 0
    return max(lobby.snowballs.keys()) + 1


def create_snowball(lobby, pos, angle, force):
    ball_id = create_snowball_id(lobby)
    snowball = player.Snowball(ball_id)
    direction = vec.from_direction(angle, 1)
    velocity = vec.mul(direction, force*MAX_THROWING_FORCE)
    snowball.position = vec.add(pos, vec.mul(direction, SNOWBALL_SPAWN_DISTANCE))
    snowball.velocity = velocity
    lobby.snowballs[ball_id] = snowball
